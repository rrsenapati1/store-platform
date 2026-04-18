from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Callable


SERVICE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))


VerifyCallable = Callable[..., dict[str, object]]
LocalVerifyCallable = Callable[[], dict[str, object]]
PerformanceVerifyCallable = Callable[[], dict[str, object]]


def _load_script_module(script_name: str, module_name: str):
    script_path = SERVICE_ROOT / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _default_local_verify() -> dict[str, object]:
    command = [sys.executable, str(SERVICE_ROOT / "scripts" / "verify_control_plane.py")]
    completed = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "status": "passed" if completed.returncode == 0 else "failed",
        "command": " ".join(command),
        "summary": (completed.stdout or completed.stderr).strip() or f"exit code {completed.returncode}",
    }


def _default_performance_validate(*, output_path: Path) -> dict[str, object]:
    command = [
        sys.executable,
        str(SERVICE_ROOT / "scripts" / "validate_performance_foundation.py"),
        "--iterations",
        "3",
        "--output-path",
        str(output_path),
    ]
    completed = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    summary = (completed.stdout or completed.stderr).strip() or f"exit code {completed.returncode}"
    payload: dict[str, object]
    if output_path.exists():
        payload = json.loads(output_path.read_text(encoding="utf-8"))
    else:
        payload = {"status": "failed" if completed.returncode != 0 else "passed"}
    payload["status"] = "passed" if completed.returncode == 0 and payload.get("status") == "passed" else "failed"
    payload["command"] = " ".join(command)
    failing_scenarios = list(payload.get("failing_scenarios") or [])
    scenario_results = list(payload.get("scenario_results") or [])
    payload["summary"] = payload.get("summary") or (
        f"{len(scenario_results)} scenarios passed"
        if not failing_scenarios and scenario_results
        else f"{len(failing_scenarios)} scenarios failed: {', '.join(failing_scenarios)}"
    )
    return payload


def _stringify_domains(domains: list[str]) -> str:
    return ", ".join(domains) if domains else "none"


def _render_markdown(
    *,
    expected_release_version: str | None,
    expected_environment: str | None,
    release_owner: str | None,
    date_text: str,
    local_result: dict[str, object],
    performance_result: dict[str, object],
    restore_drill_result: dict[str, object] | None,
    deployed_result: dict[str, object],
    certification_result: dict[str, object],
) -> str:
    deployed_domains = list(deployed_result.get("legacy_remaining_domains") or [])
    final_status = str(certification_result.get("status") or "blocked")
    restore_drill_lines = [
        "## Recovery Evidence",
        "",
        "- Restore drill: not-run",
        "",
    ]
    if restore_drill_result is not None:
        restore_drill_source = dict(restore_drill_result.get("source") or {})
        restore_drill_manifest = dict(restore_drill_result.get("restored_manifest") or {})
        restore_drill_lines = [
            "## Recovery Evidence",
            "",
            f"- restore drill status: {restore_drill_result.get('status')}",
            f"- dump key: {restore_drill_source.get('dump_key') or ''}",
            f"- metadata key: {restore_drill_source.get('metadata_key') or ''}",
            f"- restored environment: {restore_drill_manifest.get('environment') or ''}",
            f"- restored release version: {restore_drill_manifest.get('release_version') or ''}",
            "",
        ]
    return "\n".join(
        [
            "# Release Candidate Evidence",
            "",
            f"Generated: {date_text}",
            "",
            "## Candidate Metadata",
            "",
            f"- Version: {expected_release_version or deployed_result.get('release_version') or ''}",
            f"- Environment: {expected_environment or deployed_result.get('environment') or ''}",
            f"- Release owner: {release_owner or ''}",
            f"- Date: {date_text}",
            "",
            "## Verification Evidence",
            "",
            f"- Local verification command: {local_result.get('command') or 'not-run'}",
            f"  - result: {local_result.get('status')}",
            f"  - summary: {local_result.get('summary') or 'not-run'}",
            f"- Performance validation command: {performance_result.get('command') or 'not-run'}",
            f"  - result: {performance_result.get('status')}",
            f"  - summary: {performance_result.get('summary') or 'not-run'}",
            "- Deployed verification command: python services/control-plane-api/scripts/verify_deployed_control_plane.py --base-url ... --expected-environment ... --expected-release-version ...",
            f"  - result: {deployed_result.get('status')}",
            f"  - summary: environment={deployed_result.get('environment')} release_version={deployed_result.get('release_version')}",
            "- Release-candidate certification command: python services/control-plane-api/scripts/certify_release_candidate.py --base-url ... --expected-environment ... --expected-release-version ...",
            f"  - result: {certification_result.get('status')}",
            "",
            *restore_drill_lines,
            "## Authority / Cutover Evidence",
            "",
            f"- `legacy_write_mode`: {deployed_result.get('legacy_write_mode')}",
            f"- `legacy_remaining_domains`: {_stringify_domains(deployed_domains)}",
            "",
            "## Final Decision",
            "",
            f"- Status: {final_status}",
            "- Notes: Human sign-off and beta evidence are still required for operational approval.",
            "",
        ]
    )


def generate_release_candidate_evidence(
    *,
    base_url: str,
    expected_environment: str | None = None,
    expected_release_version: str | None = None,
    release_owner: str | None = None,
    output_path: Path,
    restore_drill_report_path: Path | None = None,
    bearer_token: str | None = None,
    run_local_verification: bool = True,
    run_performance_validation: bool = True,
    local_verify: LocalVerifyCallable | None = None,
    performance_validate: PerformanceVerifyCallable | None = None,
    verify_deployed: VerifyCallable | None = None,
    certify_release_candidate: VerifyCallable | None = None,
    date_text: str | None = None,
) -> dict[str, object]:
    local_verifier = local_verify or _default_local_verify
    deployed_verifier = verify_deployed or _load_script_module(
        "verify_deployed_control_plane.py",
        "verify_deployed_control_plane_script",
    ).verify_deployed_control_plane
    certifier = certify_release_candidate or _load_script_module(
        "certify_release_candidate.py",
        "certify_release_candidate_script",
    ).certify_release_candidate

    effective_date_text = date_text or str(date.today())
    local_result = (
        local_verifier()
        if run_local_verification
        else {"status": "skipped", "command": "not-run", "summary": "not-run"}
    )
    performance_output_path = output_path.with_name(f"{output_path.stem}-performance.json")
    performance_result = (
        (performance_validate or (lambda: _default_performance_validate(output_path=performance_output_path)))()
        if run_performance_validation
        else {"status": "skipped", "command": "not-run", "summary": "not-run"}
    )
    restore_drill_result = (
        json.loads(restore_drill_report_path.read_text(encoding="utf-8"))
        if restore_drill_report_path is not None
        else None
    )
    deployed_result = deployed_verifier(
        base_url=base_url,
        expected_environment=expected_environment,
        expected_release_version=expected_release_version,
        bearer_token=bearer_token,
    )
    certification_result = certifier(
        base_url=base_url,
        expected_environment=expected_environment,
        expected_release_version=expected_release_version,
        bearer_token=bearer_token,
        performance_result=None if performance_result.get("status") == "skipped" else performance_result,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        _render_markdown(
            expected_release_version=expected_release_version,
            expected_environment=expected_environment,
            release_owner=release_owner,
            date_text=effective_date_text,
            local_result=local_result,
            performance_result=performance_result,
            restore_drill_result=restore_drill_result,
            deployed_result=deployed_result,
            certification_result=certification_result,
        ),
        encoding="utf-8",
    )

    return {
        "final_status": certification_result.get("status"),
        "output_path": str(output_path),
        "local_result": local_result,
        "performance_result": performance_result,
        "restore_drill_result": restore_drill_result,
        "deployed_result": deployed_result,
        "certification_result": certification_result,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Store release-candidate evidence from verification commands.")
    parser.add_argument("--base-url", required=True, help="Public control-plane base URL, for example https://control.store.korsenex.com")
    parser.add_argument("--expected-environment", help="Expected deployment environment label such as staging or prod.")
    parser.add_argument("--expected-release-version", help="Expected release version reported by the deployment.")
    parser.add_argument("--release-owner", help="Release owner recorded in the evidence file.")
    parser.add_argument("--output-path", help="Markdown file path for the generated evidence document.")
    parser.add_argument("--restore-drill-report", help="Optional JSON restore-drill report path produced by run_restore_drill.py.")
    parser.add_argument("--bearer-token", help="Optional bearer token used to verify /v1/auth/me against the deployment.")
    parser.add_argument("--skip-local-verification", action="store_true", help="Skip the local verify_control_plane.py run.")
    parser.add_argument("--skip-performance-validation", action="store_true", help="Skip the local performance validation run.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path(args.output_path) if args.output_path else (
        REPO_ROOT
        / "docs"
        / "launch"
        / "evidence"
        / f"{(args.expected_environment or 'unknown').strip()}-{(args.expected_release_version or 'unknown').strip().replace('/', '-')}.md"
    )
    result = generate_release_candidate_evidence(
        base_url=args.base_url,
        expected_environment=args.expected_environment,
        expected_release_version=args.expected_release_version,
        release_owner=args.release_owner,
        output_path=output_path,
        restore_drill_report_path=Path(args.restore_drill_report) if args.restore_drill_report else None,
        bearer_token=args.bearer_token,
        run_local_verification=not args.skip_local_verification,
        run_performance_validation=not args.skip_performance_validation,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
