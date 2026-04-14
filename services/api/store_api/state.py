from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .inventory import InventoryLedgerService


@dataclass(slots=True)
class AppState:
    tenants: dict[str, dict[str, Any]] = field(default_factory=dict)
    branches: dict[str, dict[str, Any]] = field(default_factory=dict)
    products: dict[str, dict[str, Any]] = field(default_factory=dict)
    catalog_overrides: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)
    reorder_rules: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)
    suppliers: dict[str, dict[str, Any]] = field(default_factory=dict)
    customers: dict[str, dict[str, Any]] = field(default_factory=dict)
    cash_sessions: dict[str, dict[str, Any]] = field(default_factory=dict)
    purchase_orders: dict[str, dict[str, Any]] = field(default_factory=dict)
    goods_receipts: dict[str, dict[str, Any]] = field(default_factory=dict)
    purchase_invoices: dict[str, dict[str, Any]] = field(default_factory=dict)
    vendor_disputes: dict[str, dict[str, Any]] = field(default_factory=dict)
    supplier_payments: dict[str, dict[str, Any]] = field(default_factory=dict)
    transfers: dict[str, dict[str, Any]] = field(default_factory=dict)
    sale_returns: dict[str, dict[str, Any]] = field(default_factory=dict)
    credit_notes: dict[str, dict[str, Any]] = field(default_factory=dict)
    exchange_orders: dict[str, dict[str, Any]] = field(default_factory=dict)
    supplier_returns: dict[str, dict[str, Any]] = field(default_factory=dict)
    support_sessions: dict[str, dict[str, Any]] = field(default_factory=dict)
    stock_counts: dict[str, dict[str, Any]] = field(default_factory=dict)
    staff_assignments: dict[str, dict[str, Any]] = field(default_factory=dict)
    devices: dict[str, dict[str, Any]] = field(default_factory=dict)
    print_jobs: dict[str, dict[str, Any]] = field(default_factory=dict)
    batch_lots: dict[str, dict[str, Any]] = field(default_factory=dict)
    invoices: dict[str, dict[str, Any]] = field(default_factory=dict)
    sales: dict[str, dict[str, Any]] = field(default_factory=dict)
    gst_exports: dict[str, dict[str, Any]] = field(default_factory=dict)
    irn_attachments: dict[str, dict[str, Any]] = field(default_factory=dict)
    invoice_sequences: dict[tuple[str, str], int] = field(default_factory=dict)
    inventory: InventoryLedgerService = field(default_factory=InventoryLedgerService)
    sync_records: list[dict[str, Any]] = field(default_factory=list)
    audit_logs: list[dict[str, Any]] = field(default_factory=list)


def snapshot_state(state: AppState) -> dict[str, Any]:
    return {
        "tenants": state.tenants,
        "branches": state.branches,
        "products": state.products,
        "catalog_overrides": list(state.catalog_overrides.values()),
        "reorder_rules": list(state.reorder_rules.values()),
        "suppliers": state.suppliers,
        "customers": state.customers,
        "cash_sessions": state.cash_sessions,
        "purchase_orders": state.purchase_orders,
        "goods_receipts": state.goods_receipts,
        "purchase_invoices": state.purchase_invoices,
        "vendor_disputes": state.vendor_disputes,
        "supplier_payments": state.supplier_payments,
        "transfers": state.transfers,
        "sale_returns": state.sale_returns,
        "credit_notes": state.credit_notes,
        "exchange_orders": state.exchange_orders,
        "supplier_returns": state.supplier_returns,
        "support_sessions": state.support_sessions,
        "stock_counts": state.stock_counts,
        "staff_assignments": state.staff_assignments,
        "devices": state.devices,
        "print_jobs": state.print_jobs,
        "batch_lots": state.batch_lots,
        "invoices": state.invoices,
        "sales": state.sales,
        "gst_exports": state.gst_exports,
        "irn_attachments": state.irn_attachments,
        "invoice_sequences": [
            {"scope": scope, "fiscal_year": fiscal_year, "value": value}
            for (scope, fiscal_year), value in state.invoice_sequences.items()
        ],
        "inventory": {"entries": state.inventory.entries},
        "sync_records": state.sync_records,
        "audit_logs": state.audit_logs,
    }


def restore_state(snapshot: dict[str, Any]) -> AppState:
    state = AppState()
    state.tenants = dict(snapshot.get("tenants", {}))
    state.branches = dict(snapshot.get("branches", {}))
    state.products = dict(snapshot.get("products", {}))
    state.catalog_overrides = {
        (entry["branch_id"], entry["product_id"]): entry for entry in snapshot.get("catalog_overrides", [])
    }
    state.reorder_rules = {
        (entry["branch_id"], entry["product_id"]): entry for entry in snapshot.get("reorder_rules", [])
    }
    state.suppliers = dict(snapshot.get("suppliers", {}))
    state.customers = dict(snapshot.get("customers", {}))
    state.cash_sessions = dict(snapshot.get("cash_sessions", {}))
    state.purchase_orders = dict(snapshot.get("purchase_orders", {}))
    state.goods_receipts = dict(snapshot.get("goods_receipts", {}))
    state.purchase_invoices = dict(snapshot.get("purchase_invoices", {}))
    state.vendor_disputes = dict(snapshot.get("vendor_disputes", {}))
    state.supplier_payments = dict(snapshot.get("supplier_payments", {}))
    state.transfers = dict(snapshot.get("transfers", {}))
    state.sale_returns = dict(snapshot.get("sale_returns", {}))
    state.credit_notes = dict(snapshot.get("credit_notes", {}))
    state.exchange_orders = dict(snapshot.get("exchange_orders", {}))
    state.supplier_returns = dict(snapshot.get("supplier_returns", {}))
    state.support_sessions = dict(snapshot.get("support_sessions", {}))
    state.stock_counts = dict(snapshot.get("stock_counts", {}))
    state.staff_assignments = dict(snapshot.get("staff_assignments", {}))
    state.devices = dict(snapshot.get("devices", {}))
    state.print_jobs = dict(snapshot.get("print_jobs", {}))
    state.batch_lots = dict(snapshot.get("batch_lots", {}))
    state.invoices = dict(snapshot.get("invoices", {}))
    state.sales = dict(snapshot.get("sales", {}))
    state.gst_exports = dict(snapshot.get("gst_exports", {}))
    state.irn_attachments = dict(snapshot.get("irn_attachments", {}))
    state.invoice_sequences = {
        (entry["scope"], entry["fiscal_year"]): int(entry["value"]) for entry in snapshot.get("invoice_sequences", [])
    }
    state.inventory = InventoryLedgerService(entries=[dict(entry) for entry in snapshot.get("inventory", {}).get("entries", [])])
    state.sync_records = [dict(entry) for entry in snapshot.get("sync_records", [])]
    state.audit_logs = [dict(entry) for entry in snapshot.get("audit_logs", [])]
    return state
