from __future__ import annotations

import json
from pathlib import Path


REQUIRED_SIGN_OFFS = (
    "backend_owner",
    "runtime_owner",
    "infra_owner",
    "support_owner",
    "release_owner",
)

REQUIRED_PILOT_CHECKS = (
    "owner_web_onboarding",
    "desktop_install_activation",
    "runtime_hardware_validation",
)


def _as_string(value: object) -> str:
    return str(value or "").strip()


def _check_payload(
    *,
    name: str,
    passed: bool,
    observed_value: object,
    reason: str,
) -> dict[str, object]:
    return {
        "name": name,
        "status": "passed" if passed else "failed",
        "observed_value": observed_value,
        "reason": reason,
    }


def _pilot_checks_passed(pilot: dict[str, object]) -> bool:
    checks = dict(pilot.get("surface_checks") or {})
    required_checks_ok = all(checks.get(check_name) == "passed" for check_name in REQUIRED_PILOT_CHECKS)
    return required_checks_ok and bool(checks.get("offline_continuity_reviewed"))


def _accepted_issue_documented(issue: dict[str, object]) -> bool:
    return all(
        _as_string(issue.get(field_name))
        for field_name in ("owner", "workaround", "target_release")
    )


def _approved_sign_off(sign_off: dict[str, object]) -> bool:
    return (
        _as_string(sign_off.get("status")).lower() == "approved"
        and _as_string(sign_off.get("approver"))
        and _as_string(sign_off.get("date"))
    )


def _render_checks_markdown(checks: list[dict[str, object]]) -> list[str]:
    lines = ["## Checks", ""]
    for check in checks:
        lines.append(
            f"- `{check['name']}`: {check['status']} ({check.get('reason') or 'no reason'})"
        )
    lines.append("")
    return lines


def _render_pilots_markdown(pilots: list[dict[str, object]]) -> list[str]:
    lines = ["## Pilot Evidence", ""]
    if not pilots:
        lines.extend(["- none", ""])
        return lines
    for pilot in pilots:
        lines.append(
            f"- `{pilot.get('tenant_id')}/{pilot.get('branch_id')}`: {pilot.get('outcome') or 'unknown'}"
        )
        surface_checks = dict(pilot.get("surface_checks") or {})
        lines.append(
            "  - surface checks: "
            + ", ".join(
                [
                    f"{check_name}={surface_checks.get(check_name)}"
                    for check_name in (*REQUIRED_PILOT_CHECKS, "offline_continuity_reviewed")
                ]
            )
        )
    lines.append("")
    return lines


def _render_issues_markdown(issues: list[dict[str, object]]) -> list[str]:
    lines = ["## Known Issues", ""]
    if not issues:
        lines.extend(["- none", ""])
        return lines
    for issue in issues:
        lines.append(
            f"- `{issue.get('id') or 'untracked'}`: severity={issue.get('severity') or 'unknown'} status={issue.get('status') or 'unknown'}"
        )
    lines.append("")
    return lines


def _render_sign_offs_markdown(sign_offs: dict[str, dict[str, object]]) -> list[str]:
    lines = ["## Sign-Offs", ""]
    for sign_off_name in REQUIRED_SIGN_OFFS:
        sign_off = dict(sign_offs.get(sign_off_name) or {})
        lines.append(
            f"- `{sign_off_name}`: {sign_off.get('status') or 'missing'} by {sign_off.get('approver') or 'unassigned'}"
        )
    lines.append("")
    return lines


def assess_launch_readiness(
    *,
    manifest: dict[str, object],
    release_gate_report: dict[str, object],
    generated_at: str,
) -> dict[str, object]:
    release_version = _as_string(manifest.get("release_version"))
    environment = _as_string(manifest.get("environment"))
    release_owner = _as_string(manifest.get("release_owner"))
    beta_owner = _as_string(manifest.get("beta_owner"))
    candidate_date = _as_string(manifest.get("candidate_date"))

    pilots = [dict(pilot or {}) for pilot in list(manifest.get("pilots") or [])]
    successful_pilots = [pilot for pilot in pilots if _as_string(pilot.get("outcome")).lower() == "passed"]
    issues = [dict(issue or {}) for issue in list(manifest.get("issues") or [])]
    sign_offs = {
        sign_off_name: dict(sign_offs_payload or {})
        for sign_off_name, sign_offs_payload in dict(manifest.get("sign_offs") or {}).items()
    }

    release_gate_status = _as_string(release_gate_report.get("status")).lower()
    certification_status = _as_string(release_gate_report.get("certification_status")).lower()
    gate_release_version = _as_string(release_gate_report.get("release_version"))
    gate_environment = _as_string(release_gate_report.get("environment"))

    release_gate_passed = release_gate_status == "passed" and certification_status == "approved"
    manifest_matches_gate = True
    if gate_release_version:
        manifest_matches_gate = manifest_matches_gate and gate_release_version == release_version
    if gate_environment:
        manifest_matches_gate = manifest_matches_gate and gate_environment == environment

    successful_pilot_count = len(successful_pilots)
    pilot_surface_checks_complete = successful_pilot_count > 0 and all(
        _pilot_checks_passed(pilot) for pilot in successful_pilots
    )
    severity_one_blockers_cleared = not any(
        _as_string(issue.get("severity")).lower() == "sev1"
        and _as_string(issue.get("status")).lower() != "resolved"
        for issue in issues
    )
    accepted_issues_documented = all(
        _accepted_issue_documented(issue)
        for issue in issues
        if _as_string(issue.get("status")).lower() == "accepted"
    )
    approved_sign_off_count = sum(
        1
        for sign_off_name in REQUIRED_SIGN_OFFS
        if _approved_sign_off(sign_offs.get(sign_off_name, {}))
    )
    required_sign_offs_complete = approved_sign_off_count == len(REQUIRED_SIGN_OFFS)

    checks = [
        _check_payload(
            name="release_gate_passed",
            passed=release_gate_passed,
            observed_value={
                "release_gate_status": release_gate_status or "missing",
                "certification_status": certification_status or "missing",
            },
            reason="strict technical release gate must already be approved",
        ),
        _check_payload(
            name="manifest_matches_release_gate",
            passed=manifest_matches_gate,
            observed_value={
                "manifest_release_version": release_version,
                "manifest_environment": environment,
                "gate_release_version": gate_release_version or "not-reported",
                "gate_environment": gate_environment or "not-reported",
            },
            reason="launch manifest should align with the strict release-gate version and environment when reported",
        ),
        _check_payload(
            name="beta_pilot_completed",
            passed=successful_pilot_count > 0,
            observed_value=successful_pilots,
            reason="at least one successful packaged branch pilot must be recorded",
        ),
        _check_payload(
            name="pilot_surface_checks_complete",
            passed=pilot_surface_checks_complete,
            observed_value=[pilot.get("surface_checks") for pilot in successful_pilots],
            reason="successful pilots must include onboarding, install/activation, hardware validation, and offline review",
        ),
        _check_payload(
            name="severity_one_blockers_cleared",
            passed=severity_one_blockers_cleared,
            observed_value=issues,
            reason="no unresolved severity-1 blockers can remain at launch review",
        ),
        _check_payload(
            name="accepted_issues_documented",
            passed=accepted_issues_documented,
            observed_value=issues,
            reason="accepted launch issues must include owner, workaround, and target release",
        ),
        _check_payload(
            name="required_sign_offs_complete",
            passed=required_sign_offs_complete,
            observed_value=sign_offs,
            reason="backend, runtime, infra, support, and release owners must approve explicitly",
        ),
    ]
    failing_checks = [str(check["name"]) for check in checks if check["status"] != "passed"]
    status = "ready" if not failing_checks else "hold"
    summary = (
        f"launch readiness ready for {environment}/{release_version}"
        if status == "ready"
        else f"launch readiness hold with failing checks: {', '.join(failing_checks)}"
    )

    return {
        "status": status,
        "generated_at": generated_at,
        "summary": summary,
        "release_version": release_version,
        "environment": environment,
        "release_owner": release_owner,
        "beta_owner": beta_owner,
        "candidate_date": candidate_date,
        "release_gate_status": release_gate_status or "missing",
        "certification_status": certification_status or "missing",
        "release_gate_summary": _as_string(release_gate_report.get("summary")),
        "pilot_count": len(pilots),
        "successful_pilot_count": successful_pilot_count,
        "approved_sign_off_count": approved_sign_off_count,
        "checks": checks,
        "failing_checks": failing_checks,
        "pilots": pilots,
        "issues": issues,
        "sign_offs": sign_offs,
        "report_paths": dict(release_gate_report.get("report_paths") or {}),
    }


def render_launch_readiness_markdown(report: dict[str, object]) -> str:
    lines = [
        "# V2 Launch Readiness Report",
        "",
        f"- Generated: {report.get('generated_at') or ''}",
        f"- Version: {report.get('release_version') or ''}",
        f"- Environment: {report.get('environment') or ''}",
        f"- Release owner: {report.get('release_owner') or ''}",
        f"- Beta owner: {report.get('beta_owner') or ''}",
        f"- Candidate date: {report.get('candidate_date') or ''}",
        f"- Status: {report.get('status') or 'hold'}",
        f"- Summary: {report.get('summary') or ''}",
        "",
        "## Technical Gate",
        "",
        f"- release gate passed: {report.get('release_gate_status') or 'missing'}",
        f"- certification status: {report.get('certification_status') or 'missing'}",
        f"- release gate summary: {report.get('release_gate_summary') or 'none'}",
        "",
    ]
    lines.extend(_render_checks_markdown([dict(check or {}) for check in list(report.get("checks") or [])]))
    lines.extend(_render_pilots_markdown([dict(pilot or {}) for pilot in list(report.get("pilots") or [])]))
    lines.extend(_render_issues_markdown([dict(issue or {}) for issue in list(report.get("issues") or [])]))
    lines.extend(
        _render_sign_offs_markdown(
            {
                key: dict(value or {})
                for key, value in dict(report.get("sign_offs") or {}).items()
            }
        )
    )
    return "\n".join(lines)


def write_launch_readiness_report(
    report: dict[str, object],
    *,
    output_path: Path,
    markdown_output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    markdown_output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_output_path.write_text(render_launch_readiness_markdown(report), encoding="utf-8")


def build_launch_readiness_report(
    *,
    manifest_path: Path,
    release_gate_report_path: Path,
    output_path: Path,
    markdown_output_path: Path | None = None,
    generated_at: str,
) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    release_gate_report = json.loads(release_gate_report_path.read_text(encoding="utf-8"))
    report = assess_launch_readiness(
        manifest=manifest,
        release_gate_report=release_gate_report,
        generated_at=generated_at,
    )
    effective_markdown_output_path = markdown_output_path or output_path.with_suffix(".md")
    write_launch_readiness_report(
        report,
        output_path=output_path,
        markdown_output_path=effective_markdown_output_path,
    )
    return {
        "status": report["status"],
        "summary": report["summary"],
        "output_path": str(output_path),
        "markdown_output_path": str(effective_markdown_output_path),
    }
