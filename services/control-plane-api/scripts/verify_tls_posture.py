from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import socket
import ssl
import sys
from typing import Callable
from urllib.parse import urlparse


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from store_control_plane.tls_verification import (  # noqa: E402
    build_tls_posture_report,
    summarize_tls_posture_report,
    write_tls_posture_report,
)


TlsInspectCallable = Callable[..., dict[str, object]]


def _cert_timestamp_to_isoformat(raw_value: str | None) -> str | None:
    if not raw_value:
        return None
    seconds = ssl.cert_time_to_seconds(raw_value)
    return datetime.fromtimestamp(seconds, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _extract_subject_common_name(certificate: dict[str, object]) -> str | None:
    subject = list(certificate.get("subject") or [])
    for entry in subject:
        for key, value in entry:
            if key == "commonName":
                return str(value)
    return None


def inspect_tls_certificate(*, scheme: str, host: str, port: int, timeout_seconds: float = 10.0) -> dict[str, object]:
    if scheme != "https":
        return {
            "scheme": scheme,
            "host": host,
            "port": port,
            "subject_common_name": None,
            "san_dns_names": [],
            "protocol": None,
            "cipher": None,
            "not_before": None,
            "not_after": None,
            "days_remaining": None,
        }

    context = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=timeout_seconds) as sock:
        with context.wrap_socket(sock, server_hostname=host) as tls_socket:
            certificate = tls_socket.getpeercert()
            not_after = _cert_timestamp_to_isoformat(certificate.get("notAfter"))
            days_remaining = None
            if not_after is not None:
                expiry = datetime.fromisoformat(not_after.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                days_remaining = int((expiry - now).total_seconds() // 86400)
            cipher = tls_socket.cipher()
            return {
                "scheme": scheme,
                "host": host,
                "port": port,
                "subject_common_name": _extract_subject_common_name(certificate),
                "san_dns_names": [
                    str(value)
                    for name_type, value in list(certificate.get("subjectAltName") or [])
                    if name_type == "DNS"
                ],
                "protocol": tls_socket.version(),
                "cipher": None if not cipher else cipher[0],
                "not_before": _cert_timestamp_to_isoformat(certificate.get("notBefore")),
                "not_after": not_after,
                "days_remaining": days_remaining,
            }


def verify_tls_posture(
    *,
    base_url: str,
    output_path: Path,
    min_days_remaining: int = 30,
    inspect_tls: TlsInspectCallable | None = None,
) -> dict[str, object]:
    parsed = urlparse(base_url.strip())
    if not parsed.scheme or not parsed.hostname:
        raise ValueError("base URL must include scheme and hostname")
    scheme = parsed.scheme.lower()
    port = parsed.port or (443 if scheme == "https" else 80)
    inspection = (inspect_tls or inspect_tls_certificate)(
        scheme=scheme,
        host=parsed.hostname,
        port=port,
    )
    report = build_tls_posture_report(
        expected_hostname=parsed.hostname,
        min_days_remaining=min_days_remaining,
        inspection=inspection,
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
    write_tls_posture_report(report, output_path=output_path)
    payload = report.to_dict()
    payload["output_path"] = str(output_path)
    payload["summary"] = summarize_tls_posture_report(report)
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify TLS certificate posture for a deployed Store control plane.")
    parser.add_argument("--base-url", required=True, help="Public control-plane base URL, for example https://control.store.korsenex.com")
    parser.add_argument("--output-path", required=True, help="JSON report path for the generated TLS posture evidence.")
    parser.add_argument("--min-days-remaining", type=int, default=30, help="Minimum acceptable remaining validity window in days.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = verify_tls_posture(
        base_url=args.base_url,
        output_path=Path(args.output_path),
        min_days_remaining=args.min_days_remaining,
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
