from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(slots=True)
class TlsPostureCheck:
    name: str
    status: str
    observed_value: object
    expected_value: object
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class TlsPostureReport:
    status: str
    scheme: str
    host: str
    port: int
    protocol: str | None
    cipher: str | None
    subject_common_name: str | None
    san_dns_names: list[str]
    not_before: str | None
    not_after: str | None
    days_remaining: int | None
    generated_at: str
    checks: list[TlsPostureCheck]
    failing_checks: list[str]
    summary: str

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "scheme": self.scheme,
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol,
            "cipher": self.cipher,
            "subject_common_name": self.subject_common_name,
            "san_dns_names": list(self.san_dns_names),
            "not_before": self.not_before,
            "not_after": self.not_after,
            "days_remaining": self.days_remaining,
            "generated_at": self.generated_at,
            "checks": [check.to_dict() for check in self.checks],
            "failing_checks": list(self.failing_checks),
            "summary": self.summary,
        }


def _build_check(
    *,
    name: str,
    observed_value: object,
    expected_value: object,
    passed: bool,
    reason: str,
) -> TlsPostureCheck:
    return TlsPostureCheck(
        name=name,
        status="passed" if passed else "failed",
        observed_value=observed_value,
        expected_value=expected_value,
        reason=reason,
    )


def build_tls_posture_report(
    *,
    expected_hostname: str,
    min_days_remaining: int,
    inspection: dict[str, object],
    generated_at: str,
) -> TlsPostureReport:
    scheme = str(inspection.get("scheme") or "")
    host = str(inspection.get("host") or "")
    port = int(inspection.get("port") or 0)
    subject_common_name = None if inspection.get("subject_common_name") is None else str(inspection.get("subject_common_name"))
    san_dns_names = [str(name) for name in list(inspection.get("san_dns_names") or [])]
    days_remaining = None if inspection.get("days_remaining") is None else int(inspection.get("days_remaining"))
    hostname_candidates = set(san_dns_names)
    if subject_common_name:
        hostname_candidates.add(subject_common_name)

    checks = [
        _build_check(
            name="https_required",
            observed_value=scheme,
            expected_value="https",
            passed=scheme == "https",
            reason="HTTPS required for deployed control plane",
        ),
        _build_check(
            name="hostname_match",
            observed_value=sorted(hostname_candidates),
            expected_value=expected_hostname,
            passed=expected_hostname in hostname_candidates,
            reason="certificate matches requested hostname",
        ),
        _build_check(
            name="certificate_not_expired",
            observed_value=days_remaining,
            expected_value=">= 0",
            passed=days_remaining is not None and days_remaining >= 0,
            reason="certificate not expired",
        ),
        _build_check(
            name="certificate_validity_window",
            observed_value=days_remaining,
            expected_value=f">= {min_days_remaining}",
            passed=days_remaining is not None and days_remaining >= min_days_remaining,
            reason="certificate validity window meets minimum",
        ),
    ]
    failing_checks = [check.name for check in checks if check.status != "passed"]
    summary = summarize_tls_posture_checks(failing_checks=failing_checks)
    return TlsPostureReport(
        status="passed" if not failing_checks else "failed",
        scheme=scheme,
        host=host,
        port=port,
        protocol=None if inspection.get("protocol") is None else str(inspection.get("protocol")),
        cipher=None if inspection.get("cipher") is None else str(inspection.get("cipher")),
        subject_common_name=subject_common_name,
        san_dns_names=san_dns_names,
        not_before=None if inspection.get("not_before") is None else str(inspection.get("not_before")),
        not_after=None if inspection.get("not_after") is None else str(inspection.get("not_after")),
        days_remaining=days_remaining,
        generated_at=generated_at,
        checks=checks,
        failing_checks=failing_checks,
        summary=summary,
    )


def summarize_tls_posture_checks(*, failing_checks: list[str]) -> str:
    if not failing_checks:
        return "tls posture verified"
    return f"{len(failing_checks)} checks failed: {', '.join(failing_checks)}"


def summarize_tls_posture_report(report: TlsPostureReport) -> str:
    return summarize_tls_posture_checks(failing_checks=report.failing_checks)


def write_tls_posture_report(report: TlsPostureReport, *, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
