from __future__ import annotations


def _money(value: float) -> float:
    return round(float(value), 2)


def build_platform_tenant_summary(
    *,
    tenant: dict[str, object],
    branch_count: int,
    sales_invoice_total: float,
    purchase_invoice_total: float,
) -> dict[str, object]:
    return {
        "tenant_id": tenant["id"],
        "tenant_name": tenant["name"],
        "status": tenant.get("status", "ACTIVE"),
        "branch_count": branch_count,
        "sales_invoice_total": _money(sales_invoice_total),
        "purchase_invoice_total": _money(purchase_invoice_total),
    }


def build_platform_branch_overview(
    *,
    branch: dict[str, object],
    sales_invoice_total: float,
    purchase_invoice_total: float,
    pending_irn_invoices: int,
) -> dict[str, object]:
    return {
        "branch_id": branch["id"],
        "branch_name": branch["name"],
        "sales_invoice_total": _money(sales_invoice_total),
        "purchase_invoice_total": _money(purchase_invoice_total),
        "pending_irn_invoices": pending_irn_invoices,
    }


def build_support_session(
    *,
    session_id: str,
    tenant_id: str,
    branch_ids: list[str],
) -> dict[str, object]:
    return {
        "id": session_id,
        "tenant_id": tenant_id,
        "branch_ids": branch_ids,
        "access_mode": "READ_ONLY",
    }
