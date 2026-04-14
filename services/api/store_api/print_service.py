from __future__ import annotations

from typing import Any


def _money(value: float) -> str:
    return f"{float(value):.2f}"


def build_invoice_receipt_lines(
    *,
    invoice_number: str,
    customer_name: str,
    customer_gstin: str | None,
    items: list[dict[str, Any]],
    totals: dict[str, float],
    irn_status: str,
) -> list[str]:
    lines = [
        "STORE TAX INVOICE",
        f"Invoice: {invoice_number}",
        f"Customer: {customer_name}",
    ]
    if customer_gstin:
        lines.append(f"GSTIN: {customer_gstin}")
    for item in items:
        lines.append(
            f"{item['name']} x{item['qty']} @ {_money(item['unit_price'])} = {_money(item['line_total'])}"
        )
    lines.append(f"Subtotal: {_money(totals['subtotal'])}")
    lines.append(f"CGST: {_money(totals['cgst'])}")
    lines.append(f"SGST: {_money(totals['sgst'])}")
    lines.append(f"IGST: {_money(totals['igst'])}")
    lines.append(f"Grand Total: {_money(totals['grand_total'])}")
    lines.append(f"IRN Status: {irn_status}")
    return lines


def build_print_job(
    *,
    job_id: str,
    tenant_id: str,
    branch_id: str,
    device_id: str,
    job_type: str,
    copies: int,
    payload: dict[str, Any],
    actor_roles: list[str],
) -> dict[str, Any]:
    return {
        "id": job_id,
        "tenant_id": tenant_id,
        "branch_id": branch_id,
        "device_id": device_id,
        "job_type": job_type,
        "copies": copies,
        "status": "QUEUED",
        "failure_reason": None,
        "actor_roles": actor_roles,
        "payload": payload,
    }


def complete_print_job(*, job: dict[str, Any], status: str, failure_reason: str | None = None) -> dict[str, Any]:
    job["status"] = status
    job["failure_reason"] = failure_reason
    return job
