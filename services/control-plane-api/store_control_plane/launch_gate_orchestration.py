from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from .config import Settings
from .launch_readiness import build_launch_readiness_report
from .release_evidence_bundle import build_release_evidence_bundle
from .release_evidence_publication import publish_release_evidence_bundle
from .release_gate_orchestration import run_release_gate
from .ops.release_evidence_retention import run_release_evidence_retention
from .ops.release_evidence_retrieval import verify_retained_release_evidence


Runner = Callable[..., Any]


def _as_payload(value: Any) -> dict[str, object]:
    if hasattr(value, "to_dict"):
        payload = value.to_dict()
        if isinstance(payload, dict):
            return payload
    if isinstance(value, dict):
        return value
    raise TypeError(f"unsupported result payload type: {type(value)!r}")


def write_v2_launch_gate_report(payload: dict[str, object], *, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def run_v2_launch_gate(
    *,
    base_url: str,
    expected_environment: str,
    expected_release_version: str,
    release_owner: str,
    output_dir: Path,
    launch_manifest_path: Path,
    admin_bearer_token: str,
    branch_bearer_token: str,
    tenant_id: str,
    branch_id: str,
    product_id: str,
    dump_key: str,
    metadata_key: str,
    target_database_url: str,
    bearer_token: str | None = None,
    image_refs: list[str] | None = None,
    vulnerability_exceptions_path: Path | None = None,
    retain_evidence_offsite: bool = False,
    verify_retained_evidence: bool = False,
    verify_smoke_restore_drill: bool = False,
    allow_restore_environment_mismatch: bool = False,
    settings_factory: Callable[[], Settings] | None = None,
    run_release_gate: Runner = run_release_gate,
    build_launch_readiness_report: Runner = build_launch_readiness_report,
    build_release_evidence_bundle: Runner = build_release_evidence_bundle,
    publish_release_evidence_bundle: Runner = publish_release_evidence_bundle,
    retain_release_evidence: Runner = run_release_evidence_retention,
    verify_retained_release_evidence: Runner = verify_retained_release_evidence,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    technical_gate_dir = output_dir / "technical-gate"
    launch_dir = output_dir / "launch-readiness"
    launch_bundle_dir = output_dir / "launch-bundle"
    publication_dir = output_dir / "published"
    retrieved_dir = output_dir / "retrieved" / f"{expected_environment}-{expected_release_version}"
    report_path = output_dir / "v2-launch-gate-report.json"

    launch_readiness_report_path = launch_dir / "launch-readiness-report.json"
    launch_readiness_markdown_path = launch_dir / "launch-readiness-report.md"

    technical_gate_result = _as_payload(
        run_release_gate(
            base_url=base_url,
            expected_environment=expected_environment,
            expected_release_version=expected_release_version,
            release_owner=release_owner,
            output_dir=technical_gate_dir,
            admin_bearer_token=admin_bearer_token,
            branch_bearer_token=branch_bearer_token,
            tenant_id=tenant_id,
            branch_id=branch_id,
            product_id=product_id,
            dump_key=dump_key,
            metadata_key=metadata_key,
            target_database_url=target_database_url,
            bearer_token=bearer_token,
            image_refs=list(image_refs or []),
            vulnerability_exceptions_path=vulnerability_exceptions_path,
            retain_evidence_offsite=False,
            verify_retained_evidence=False,
            verify_smoke_restore_drill=verify_smoke_restore_drill,
            allow_restore_environment_mismatch=allow_restore_environment_mismatch,
        )
    )

    technical_report_path = Path(str(technical_gate_result["report_path"]))
    launch_readiness_result = _as_payload(
        build_launch_readiness_report(
            manifest_path=launch_manifest_path,
            release_gate_report_path=technical_report_path,
            output_path=launch_readiness_report_path,
            markdown_output_path=launch_readiness_markdown_path,
            generated_at=technical_gate_result.get("generated_at") or "generated-by-v2-launch-gate",
        )
    )

    technical_report_paths = {
        label: Path(str(path))
        for label, path in dict(technical_gate_result.get("report_paths") or {}).items()
    }

    launch_bundle_result = _as_payload(
        build_release_evidence_bundle(
            output_dir=launch_bundle_dir,
            report_paths={
                "release_gate_report": technical_report_path,
                **technical_report_paths,
                "launch_readiness_report": launch_readiness_report_path,
                "launch_readiness_summary": launch_readiness_markdown_path,
                "launch_readiness_manifest": launch_manifest_path,
            },
            directory_paths={
                "technical_vulnerability_raw_output": technical_gate_dir / "raw" / "vulnerability-scans",
                "technical_sbom_artifacts": technical_gate_dir / "raw" / "sbom",
            },
        )
    )
    launch_publication_result = _as_payload(
        publish_release_evidence_bundle(
            bundle_dir=launch_bundle_dir,
            output_dir=publication_dir,
            environment=expected_environment,
            release_version=expected_release_version,
        )
    )

    settings = (settings_factory or Settings)()
    retention_result: dict[str, object] | None = None
    if retain_evidence_offsite:
        retention_plan = retain_release_evidence(
            settings,
            publication_dir=publication_dir,
            environment=expected_environment,
            release_version=expected_release_version,
        )
        retention_result = {
            "status": "retained",
            "bucket": retention_plan.bucket,
            "archive_key": retention_plan.archive_key,
            "publication_manifest_key": retention_plan.publication_manifest_key,
            "catalog_key": retention_plan.catalog_key,
            "retention_manifest_key": retention_plan.retention_manifest_key,
            "retention_manifest_path": str(retention_plan.retention_manifest_path),
        }

    retrieval_result: dict[str, object] | None = None
    if verify_retained_evidence:
        if retention_result is None:
            retrieval_result = {
                "status": "failed",
                "reason": "retained evidence verification requested but launch evidence was not retained offsite",
            }
        else:
            retrieval_result = _as_payload(
                verify_retained_release_evidence(
                    settings=settings,
                    environment=expected_environment,
                    release_version=expected_release_version,
                    output_root=retrieved_dir,
                )
            )

    status = "ready"
    summary_parts: list[str] = []
    if technical_gate_result.get("status") != "passed":
        status = "hold"
        summary_parts.append(f"technical gate {technical_gate_result.get('status') or 'blocked'}")
    else:
        summary_parts.append("technical gate passed")
    if launch_readiness_result.get("status") != "ready":
        status = "hold"
        summary_parts.append(launch_readiness_result.get("summary") or "launch readiness hold")
    else:
        summary_parts.append("launch readiness ready")
    if launch_bundle_result.get("status") != "passed":
        status = "hold"
        summary_parts.append("launch bundle failed")
    if launch_publication_result.get("status") != "published":
        status = "hold"
        summary_parts.append("launch publication failed")
    if retrieval_result is not None:
        if retrieval_result.get("status") == "passed":
            summary_parts.append("retained launch evidence verified")
        else:
            status = "hold"
            summary_parts.append("retained launch evidence verification failed")

    report_payload = {
        "status": status,
        "summary": "; ".join(summary_parts),
        "environment": expected_environment,
        "release_version": expected_release_version,
        "release_owner": release_owner,
        "launch_manifest_path": str(launch_manifest_path),
        "technical_gate_status": technical_gate_result.get("status"),
        "launch_readiness_status": launch_readiness_result.get("status"),
        "retained_evidence_status": None if retrieval_result is None else retrieval_result.get("status"),
        "technical_gate_result": technical_gate_result,
        "launch_readiness_result": launch_readiness_result,
        "launch_bundle_result": launch_bundle_result,
        "launch_publication_result": launch_publication_result,
        "offsite_retention_result": retention_result,
        "retained_evidence_result": retrieval_result,
        "report_path": str(report_path),
    }
    write_v2_launch_gate_report(report_payload, output_path=report_path)
    return report_payload
