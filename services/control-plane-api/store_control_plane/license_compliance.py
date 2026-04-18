from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
import re


SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_LICENSE_POLICY: dict[str, object] = {
    "allowed": [
        "0BSD",
        "Apache-2.0",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "CC0-1.0",
        "ISC",
        "MIT",
        "MPL-2.0",
        "OpenSSL",
        "Python-2.0",
        "Unicode-DFS-2016",
        "Zlib",
    ],
    "review_required": [
        "CDDL-1.0",
        "CDDL-1.1",
        "EPL-1.0",
        "EPL-2.0",
        "LGPL-2.1-only",
        "LGPL-2.1-or-later",
        "LGPL-3.0-only",
        "LGPL-3.0-or-later",
    ],
    "denied": [
        "AGPL-1.0-only",
        "AGPL-3.0-only",
        "AGPL-3.0-or-later",
        "BUSL-1.1",
        "Commons-Clause",
        "GPL-2.0-only",
        "GPL-2.0-or-later",
        "GPL-3.0-only",
        "GPL-3.0-or-later",
        "SSPL-1.0",
    ],
    "fail_on_unknown": True,
    "review_required_blocks_release": True,
}

LICENSE_STATUSES = ("allowed", "review_required", "denied", "unknown")

LICENSE_ALIASES = {
    "apache license 2.0": "Apache-2.0",
    "apache-2.0": "Apache-2.0",
    "bsd 2-clause license": "BSD-2-Clause",
    "bsd 3-clause license": "BSD-3-Clause",
    "isc license": "ISC",
    "mit": "MIT",
    "mit license": "MIT",
    "mozilla public license 2.0": "MPL-2.0",
    "openssl license": "OpenSSL",
    "psf-2.0": "Python-2.0",
    "python software foundation license": "Python-2.0",
    "unicode license agreement - data files and software (2016)": "Unicode-DFS-2016",
    "zlib license": "Zlib",
}


def load_license_policy(path: Path | None) -> dict[str, object]:
    effective_policy = dict(DEFAULT_LICENSE_POLICY)
    if path is None or not path.exists():
        return effective_policy
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"unsupported license policy format in {path}")
    for key in ("allowed", "review_required", "denied"):
        if key in payload:
            values = payload.get(key)
            if not isinstance(values, list):
                raise ValueError(f"license policy field {key} must be a list")
            effective_policy[key] = [str(value) for value in values]
    for key in ("fail_on_unknown", "review_required_blocks_release"):
        if key in payload:
            effective_policy[key] = bool(payload.get(key))
    return effective_policy


def load_license_exceptions(path: Path | None) -> list[dict[str, object]]:
    if path is None or not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        entries = payload.get("exceptions", [])
        if isinstance(entries, list):
            return entries
    raise ValueError(f"unsupported license exceptions format in {path}")


def _parse_exception_expiry(entry: dict[str, object]) -> date | None:
    raw_value = entry.get("expires_on")
    if not raw_value:
        return None
    return date.fromisoformat(str(raw_value))


def apply_license_exceptions(
    *,
    surface: str,
    findings: list[dict[str, object]],
    exceptions: list[dict[str, object]],
    today: date | None = None,
) -> list[dict[str, object]]:
    effective_today = today or date.today()
    filtered_findings = list(findings)

    for entry in exceptions:
        if entry.get("surface") != surface:
            continue
        expiry = _parse_exception_expiry(entry)
        if expiry is not None and expiry < effective_today:
            raise ValueError("expired license exception")
        filtered_findings = [
            finding
            for finding in filtered_findings
            if not (
                finding.get("package_or_identifier") == entry.get("package_or_identifier")
                and finding.get("license") == entry.get("license")
            )
        ]

    return filtered_findings


def _normalize_license_identifier(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    return LICENSE_ALIASES.get(normalized.lower(), normalized)


def _split_license_expression(expression: str) -> list[str]:
    collapsed = re.sub(r"[()]+", " ", expression)
    tokens = re.split(r"\s+(?:AND|OR|WITH)\s+", collapsed, flags=re.IGNORECASE)
    return [
        normalized
        for token in tokens
        if (normalized := _normalize_license_identifier(token)) is not None
    ]


def _extract_component_licenses(component: dict[str, object]) -> list[str]:
    extracted: list[str] = []
    for license_entry in list(component.get("licenses") or []):
        if not isinstance(license_entry, dict):
            continue
        expression = _normalize_license_identifier(license_entry.get("expression"))
        if expression is not None:
            extracted.extend(_split_license_expression(expression))
            continue
        license_payload = dict(license_entry.get("license") or {})
        license_id = _normalize_license_identifier(license_payload.get("id"))
        if license_id is not None:
            extracted.append(license_id)
            continue
        license_name = _normalize_license_identifier(license_payload.get("name"))
        if license_name is not None:
            extracted.append(license_name)
    deduped: list[str] = []
    for value in extracted:
        if value not in deduped:
            deduped.append(value)
    return deduped


def _classify_licenses(licenses: list[str], policy: dict[str, object]) -> str:
    if not licenses:
        return "unknown"
    allowed = set(str(value) for value in list(policy.get("allowed") or []))
    review_required = set(str(value) for value in list(policy.get("review_required") or []))
    denied = set(str(value) for value in list(policy.get("denied") or []))

    statuses: list[str] = []
    for license_value in licenses:
        if license_value in denied:
            statuses.append("denied")
        elif license_value in review_required:
            statuses.append("review_required")
        elif license_value in allowed:
            statuses.append("allowed")
        else:
            statuses.append("unknown")

    if "denied" in statuses:
        return "denied"
    if "review_required" in statuses:
        return "review_required"
    if "unknown" in statuses:
        return "unknown"
    return "allowed"


def _extract_component_identifier(component: dict[str, object]) -> str:
    for field in ("name", "bom-ref", "purl"):
        value = component.get(field)
        if value:
            return str(value)
    return "unknown-component"


def _empty_license_summary() -> dict[str, int]:
    return {status: 0 for status in LICENSE_STATUSES}


def _is_blocking_status(status: str, policy: dict[str, object]) -> bool:
    if status == "denied":
        return True
    if status == "review_required":
        return bool(policy.get("review_required_blocks_release", True))
    if status == "unknown":
        return bool(policy.get("fail_on_unknown", True))
    return False


def _build_surface_result_from_sbom(
    *,
    surface_name: str,
    artifact_path: Path,
    policy: dict[str, object],
    exceptions: list[dict[str, object]],
) -> dict[str, object]:
    if not artifact_path.exists():
        return {
            "status": "failed",
            "artifact_path": str(artifact_path),
            "component_count": 0,
            "license_summary": _empty_license_summary(),
            "findings": [],
            "failure_reason": "sbom artifact path does not exist",
        }

    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "status": "failed",
            "artifact_path": str(artifact_path),
            "component_count": 0,
            "license_summary": _empty_license_summary(),
            "findings": [],
            "failure_reason": "sbom artifact contains invalid JSON",
        }

    components = list(payload.get("components") or [])
    license_summary = _empty_license_summary()
    all_non_allowed_findings: list[dict[str, object]] = []

    for raw_component in components:
        component = dict(raw_component or {})
        licenses = _extract_component_licenses(component)
        status = _classify_licenses(licenses, policy)
        license_summary[status] += 1
        if status == "allowed":
            continue
        all_non_allowed_findings.append(
            {
                "package_or_identifier": _extract_component_identifier(component),
                "version": None if component.get("version") is None else str(component.get("version")),
                "license": ", ".join(licenses) if licenses else "UNKNOWN",
                "normalized_licenses": licenses,
                "status": status,
            }
        )

    filtered_findings = apply_license_exceptions(
        surface=surface_name,
        findings=all_non_allowed_findings,
        exceptions=exceptions,
    )
    removed_findings = [
        finding
        for finding in all_non_allowed_findings
        if finding not in filtered_findings
    ]
    for finding in removed_findings:
        status = str(finding.get("status") or "unknown")
        if status in license_summary:
            license_summary[status] -= 1
        license_summary["allowed"] += 1

    blocking_findings = [
        finding for finding in filtered_findings if _is_blocking_status(str(finding.get("status") or ""), policy)
    ]
    return {
        "status": "passed" if not blocking_findings else "failed",
        "artifact_path": str(artifact_path),
        "component_count": len(components),
        "license_summary": license_summary,
        "findings": filtered_findings,
        "failure_reason": None,
    }


def build_license_compliance_report(
    *,
    generated_at: str,
    surface_results: dict[str, dict[str, object]],
    policy: dict[str, object] | None = None,
) -> dict[str, object]:
    effective_policy = dict(DEFAULT_LICENSE_POLICY)
    if policy:
        effective_policy.update(policy)

    normalized_surfaces: dict[str, dict[str, object]] = {}
    failing_surfaces: list[str] = []

    for surface_name, raw_result in surface_results.items():
        summary = _empty_license_summary()
        summary.update(
            {
                status: int(dict(raw_result.get("license_summary") or {}).get(status, 0))
                for status in LICENSE_STATUSES
            }
        )
        normalized_result = {
            "status": str(raw_result.get("status") or "failed"),
            "artifact_path": None if raw_result.get("artifact_path") is None else str(raw_result.get("artifact_path")),
            "component_count": int(raw_result.get("component_count") or 0),
            "license_summary": summary,
            "findings": list(raw_result.get("findings") or []),
            "failure_reason": None if raw_result.get("failure_reason") is None else str(raw_result.get("failure_reason")),
        }
        normalized_surfaces[surface_name] = normalized_result
        if normalized_result["status"] != "passed":
            failing_surfaces.append(surface_name)

    summary_text = (
        f"{len(normalized_surfaces)} surfaces passed"
        if not failing_surfaces
        else f"{len(failing_surfaces)} surfaces failed: {', '.join(failing_surfaces)}"
    )
    return {
        "status": "passed" if not failing_surfaces else "failed",
        "generated_at": generated_at,
        "policy": effective_policy,
        "surfaces": normalized_surfaces,
        "failing_surfaces": failing_surfaces,
        "summary": summary_text,
    }


def write_license_compliance_report(report: dict[str, object], *, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def summarize_license_compliance_report(report: dict[str, object]) -> str:
    return str(report.get("summary") or "")


def run_license_compliance(
    *,
    sbom_report_path: Path,
    output_path: Path,
    policy_path: Path | None = None,
    exceptions_path: Path | None = None,
) -> dict[str, object]:
    sbom_report = json.loads(sbom_report_path.read_text(encoding="utf-8"))
    policy = load_license_policy(policy_path)
    exceptions = load_license_exceptions(exceptions_path)

    surface_results: dict[str, dict[str, object]] = {}
    for surface_name, raw_surface in dict(sbom_report.get("surfaces") or {}).items():
        surface = dict(raw_surface or {})
        artifact_path_value = surface.get("artifact_path")
        if str(surface.get("status") or "") != "passed":
            surface_results[surface_name] = {
                "status": "failed",
                "artifact_path": None if artifact_path_value is None else str(artifact_path_value),
                "component_count": int(surface.get("component_count") or 0),
                "license_summary": _empty_license_summary(),
                "findings": [],
                "failure_reason": "sbom surface did not pass",
            }
            continue
        if artifact_path_value is None:
            surface_results[surface_name] = {
                "status": "failed",
                "artifact_path": None,
                "component_count": int(surface.get("component_count") or 0),
                "license_summary": _empty_license_summary(),
                "findings": [],
                "failure_reason": "sbom artifact path missing from sbom report",
            }
            continue
        surface_results[surface_name] = _build_surface_result_from_sbom(
            surface_name=surface_name,
            artifact_path=Path(str(artifact_path_value)),
            policy=policy,
            exceptions=exceptions,
        )

    report = build_license_compliance_report(
        generated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        surface_results=surface_results,
        policy=policy,
    )
    write_license_compliance_report(report, output_path=output_path)
    report["output_path"] = str(output_path)
    return report
