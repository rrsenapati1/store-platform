from __future__ import annotations

from copy import deepcopy
from collections.abc import Iterable
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Annotated, Any
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .authority import MUTATION_METHODS, apply_legacy_authority_headers, build_cutover_block_response, classify_legacy_domain, resolve_legacy_write_mode
from .auth import can_perform
from .batch_tracking import build_batch_expiry_report, validate_goods_receipt_batch_lots
from .barcode_service import allocate_barcode, build_barcode_label_model, normalize_barcode
from .catalog_reporting import build_branch_catalog_records, build_central_catalog_records, build_inventory_snapshot_report
from .compliance import attach_irn_to_invoice, calculate_invoice_taxes, next_invoice_number, prepare_gst_export_job
from .customer_reporting import build_branch_customer_report, build_customer_directory_records, build_customer_history_report
from .finance import compute_cash_session_close, compute_exchange_balance, compute_tax_inclusive_total, next_credit_note_number
from .inventory import InventoryLedgerService
from .platform_admin import build_platform_branch_overview, build_platform_tenant_summary, build_support_session
from .print_reporting import build_branch_print_health_report, build_platform_print_exception_report
from .print_service import build_invoice_receipt_lines, build_print_job, complete_print_job
from .purchase_approvals import (
    build_purchase_approval_report,
    decide_purchase_order_approval,
    ensure_purchase_order_receivable,
    request_purchase_order_approval,
)
from .purchasing import compute_purchase_totals, next_purchase_invoice_number, next_supplier_credit_note_number
from .receiving import build_receiving_board, ensure_goods_receipt_not_already_created
from .replenishment import build_replenishment_records
from .reporting import build_payment_mix, build_sales_summary, build_stock_risk_report, build_top_products
from .state import AppState, restore_state, snapshot_state
from .storage import JsonStateStore
from .supplier_payables import (
    build_supplier_payables_report,
    ensure_supplier_payment_within_outstanding,
    next_supplier_payment_number,
)
from .supplier_aging import build_supplier_aging_report
from .supplier_due_schedule import build_supplier_due_schedule, compute_supplier_due_date
from .supplier_payment_activity import build_supplier_payment_activity_report
from .supplier_payment_register import build_supplier_payment_register
from .supplier_payment_run import build_supplier_payment_run
from .supplier_escalations import build_supplier_escalation_report
from .supplier_exceptions import build_supplier_exception_report
from .supplier_performance import build_supplier_performance_report
from .supplier_settlement_blockers import build_supplier_settlement_blocker_report
from .vendor_disputes import build_vendor_dispute_board
from .sync import build_pull_response, resolve_mutation_conflict
from .supplier_statements import build_supplier_statement_report
from .supplier_settlement import build_supplier_settlement_report
from .vendor_billing import build_vendor_billing_board, ensure_purchase_invoice_not_already_created


def _id() -> str:
    return uuid4().hex


def _money(value: float) -> float:
    return round(float(value), 2)


class TenantCreate(BaseModel):
    name: str


class TenantStatusUpdate(BaseModel):
    status: str = Field(pattern="^(ACTIVE|SUSPENDED)$")
    reason: str | None = None


class BranchCreate(BaseModel):
    name: str
    gstin: str | None = None


class ProductCreate(BaseModel):
    name: str
    sku_code: str
    barcode: str
    selling_price: float
    tax_rate_percent: float
    hsn_sac_code: str


class CatalogOverrideCreate(BaseModel):
    product_id: str
    selling_price: float | None = Field(default=None, gt=0)
    is_active: bool = True


class BarcodeAllocationCreate(BaseModel):
    sku_code: str
    existing_barcode: str | None = None


class BarcodeLabelPreviewCreate(BaseModel):
    product_id: str
    copies: int = Field(default=1, ge=1, le=50)


class ReorderRuleCreate(BaseModel):
    product_id: str
    min_stock: float = Field(gt=0)
    target_stock: float = Field(gt=0)


class SupplierCreate(BaseModel):
    name: str
    gstin: str | None = None
    payment_terms_days: int = Field(default=0, ge=0)


class CustomerCreate(BaseModel):
    name: str
    phone: str
    email: str | None = None
    gstin: str | None = None


class CashSessionOpenCreate(BaseModel):
    opening_float: float = Field(ge=0)


class CashSessionCloseCreate(BaseModel):
    closing_amount: float = Field(ge=0)


class PurchaseOrderLineInput(BaseModel):
    product_id: str
    quantity: float = Field(gt=0)
    unit_cost: float = Field(gt=0)


class PurchaseOrderCreate(BaseModel):
    supplier_id: str
    lines: list[PurchaseOrderLineInput]


class PurchaseOrderDecisionInput(BaseModel):
    note: str | None = None


class StaffAssignmentCreate(BaseModel):
    branch_id: str
    staff_name: str
    role: str


class DeviceRegistrationCreate(BaseModel):
    device_name: str
    session_surface: str


class InvoicePrintJobCreate(BaseModel):
    invoice_id: str
    device_id: str
    copies: int = Field(default=1, ge=1, le=5)


class BarcodePrintJobCreate(BaseModel):
    product_id: str
    device_id: str
    copies: int = Field(default=1, ge=1, le=50)


class GoodsReceiptCreate(BaseModel):
    purchase_order_id: str


class BatchLotInput(BaseModel):
    product_id: str
    batch_number: str = Field(min_length=1)
    quantity: float = Field(gt=0)
    expiry_date: str


class GoodsReceiptBatchCreate(BaseModel):
    lots: list[BatchLotInput] = Field(min_length=1)


class PurchaseInvoiceCreate(BaseModel):
    goods_receipt_id: str


class VendorDisputeCreate(BaseModel):
    goods_receipt_id: str | None = None
    purchase_invoice_id: str | None = None
    dispute_type: str = Field(min_length=1)
    note: str = Field(min_length=1)


class VendorDisputeResolve(BaseModel):
    resolution_note: str = Field(min_length=1)


class SupplierPaymentCreate(BaseModel):
    amount: float = Field(gt=0)
    payment_method: str = "bank_transfer"
    reference: str | None = None


class TransferLineInput(BaseModel):
    product_id: str
    quantity: float = Field(gt=0)


class TransferCreate(BaseModel):
    source_branch_id: str
    destination_branch_id: str
    lines: list[TransferLineInput]


class SaleLineInput(BaseModel):
    product_id: str
    quantity: float = Field(gt=0)


class SaleCreate(BaseModel):
    customer_id: str | None = None
    customer_name: str
    customer_gstin: str | None = None
    lines: list[SaleLineInput]
    payment_amount: float = Field(ge=0)
    payment_method: str = "cash"
    cash_session_id: str | None = None


class GExportCreate(BaseModel):
    invoice_id: str


class AttachIrnInput(BaseModel):
    irn: str
    ack_no: str
    signed_qr_payload: str


class ReturnLineInput(BaseModel):
    product_id: str
    quantity: float = Field(gt=0)


class SaleReturnCreate(BaseModel):
    lines: list[ReturnLineInput]
    refund_amount: float = Field(ge=0)


class RefundApprovalInput(BaseModel):
    note: str | None = None


class StockCountLineInput(BaseModel):
    product_id: str
    counted_quantity: float = Field(ge=0)


class StockCountCreate(BaseModel):
    reason: str
    lines: list[StockCountLineInput]


class ExchangeCreate(BaseModel):
    return_lines: list[ReturnLineInput]
    replacement_lines: list[SaleLineInput]
    payment_method: str = "cash"
    cash_session_id: str | None = None


class SupplierReturnCreate(BaseModel):
    lines: list[ReturnLineInput]


class ExpiryWriteOffCreate(BaseModel):
    quantity: float = Field(gt=0)
    reason: str


class SupportSessionCreate(BaseModel):
    tenant_id: str
    branch_ids: list[str] = Field(default_factory=list)


class PrintJobCompletionInput(BaseModel):
    status: str = Field(pattern="^(COMPLETED|FAILED)$")
    failure_reason: str | None = None


class SyncPushInput(BaseModel):
    record_id: str
    client_version: int
    server_version: int


def _require_capability(actor_roles: Iterable[str], capability: str) -> None:
    if not can_perform(actor_roles, capability):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")


def _require_any_capability(actor_roles: Iterable[str], capabilities: Iterable[str]) -> None:
    if not any(can_perform(actor_roles, capability) for capability in capabilities):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")


def _catalog_override_key(*, branch_id: str, product_id: str) -> tuple[str, str]:
    return branch_id, product_id


def _reorder_rule_key(*, branch_id: str, product_id: str) -> tuple[str, str]:
    return branch_id, product_id


def _list_tenant_products(state: AppState, *, tenant_id: str) -> list[dict[str, Any]]:
    return [product for product in state.products.values() if product["tenant_id"] == tenant_id]


def _build_branch_catalog(state: AppState, *, tenant_id: str, branch_id: str) -> list[dict[str, Any]]:
    products = _list_tenant_products(state, tenant_id=tenant_id)
    stock_by_product = {
        product["id"]: state.inventory.stock_on_hand(item_id=product["id"], branch_id=branch_id)
        for product in products
    }
    return build_branch_catalog_records(
        products=products,
        catalog_overrides=state.catalog_overrides,
        branch_id=branch_id,
        stock_by_product=stock_by_product,
    )


def _list_tenant_customers(state: AppState, *, tenant_id: str) -> list[dict[str, Any]]:
    return [customer for customer in state.customers.values() if customer["tenant_id"] == tenant_id]


def _find_customer(state: AppState, *, tenant_id: str, customer_id: str) -> dict[str, Any]:
    customer = state.customers.get(customer_id)
    if not customer or customer["tenant_id"] != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
    return customer


def _find_purchase_order(state: AppState, *, tenant_id: str, branch_id: str, purchase_order_id: str) -> dict[str, Any]:
    purchase_order = state.purchase_orders.get(purchase_order_id)
    if not purchase_order or purchase_order["tenant_id"] != tenant_id or purchase_order["branch_id"] != branch_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
    return purchase_order


def _find_goods_receipt(state: AppState, *, tenant_id: str, branch_id: str, goods_receipt_id: str) -> dict[str, Any]:
    goods_receipt = state.goods_receipts.get(goods_receipt_id)
    if not goods_receipt or goods_receipt["tenant_id"] != tenant_id or goods_receipt["branch_id"] != branch_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goods receipt not found")
    return goods_receipt


def _find_purchase_invoice(
    state: AppState,
    *,
    tenant_id: str,
    branch_id: str,
    purchase_invoice_id: str,
) -> dict[str, Any]:
    purchase_invoice = state.purchase_invoices.get(purchase_invoice_id)
    if not purchase_invoice or purchase_invoice["tenant_id"] != tenant_id or purchase_invoice["branch_id"] != branch_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase invoice not found")
    return purchase_invoice


def _list_branch_batch_lots(state: AppState, *, tenant_id: str, branch_id: str) -> list[dict[str, Any]]:
    return [lot for lot in state.batch_lots.values() if lot["tenant_id"] == tenant_id and lot["branch_id"] == branch_id]


def _find_batch_lot(state: AppState, *, tenant_id: str, branch_id: str, batch_lot_id: str) -> dict[str, Any]:
    batch_lot = state.batch_lots.get(batch_lot_id)
    if not batch_lot or batch_lot["tenant_id"] != tenant_id or batch_lot["branch_id"] != branch_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch lot not found")
    return batch_lot


def _build_branch_batch_report(state: AppState, *, tenant_id: str, branch_id: str) -> dict[str, Any]:
    batch_lots = _list_branch_batch_lots(state, tenant_id=tenant_id, branch_id=branch_id)
    product_ids = {lot["product_id"] for lot in batch_lots}
    products_by_id = {product_id: state.products[product_id] for product_id in product_ids}
    stock_by_product = {
        product_id: state.inventory.stock_on_hand(item_id=product_id, branch_id=branch_id)
        for product_id in product_ids
    }
    return build_batch_expiry_report(
        batch_lots=batch_lots,
        products_by_id=products_by_id,
        stock_by_product=stock_by_product,
        as_of=date.today(),
    )


def _find_product_by_barcode(state: AppState, *, tenant_id: str, barcode: str) -> dict[str, Any]:
    normalized_barcode = normalize_barcode(barcode)
    for product in state.products.values():
        if product["tenant_id"] != tenant_id:
            continue
        if normalize_barcode(product["barcode"]) == normalized_barcode:
            return product
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")


def _require_branch_device(state: AppState, *, tenant_id: str, branch_id: str, device_id: str) -> dict[str, Any]:
    device = state.devices.get(device_id)
    if not device or device["tenant_id"] != tenant_id or device["branch_id"] != branch_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return device


def _resolve_branch_pricing(state: AppState, *, branch_id: str, product_id: str) -> tuple[dict[str, Any], float]:
    product = state.products[product_id]
    override = state.catalog_overrides.get(_catalog_override_key(branch_id=branch_id, product_id=product_id))
    if override and not override["is_active"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product inactive for this branch")
    unit_price = override["selling_price"] if override and override.get("selling_price") is not None else product["selling_price"]
    return product, unit_price


def _find_sale_line(sale: dict[str, Any], *, product_id: str) -> dict[str, Any]:
    for line in sale["lines"]:
        if line["product_id"] == product_id:
            return line
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product not found on original sale")


def _find_document_line(lines: Iterable[dict[str, Any]], *, product_id: str) -> dict[str, Any]:
    for line in lines:
        if line["product_id"] == product_id:
            return line
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product not found on source document")


def _returned_supplier_quantity(state: AppState, *, purchase_invoice_id: str, product_id: str) -> float:
    return _money(
        sum(
            float(line["quantity"])
            for supplier_return in state.supplier_returns.values()
            if supplier_return["purchase_invoice_id"] == purchase_invoice_id
            for line in supplier_return["lines"]
            if line["product_id"] == product_id
        )
    )


def get_actor_roles(
    x_actor_role: Annotated[str | None, Header()] = None,
) -> list[str]:
    roles = [role.strip() for role in (x_actor_role or "").split(",") if role.strip()]
    if not roles:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing actor role")
    return roles


def _build_state_store(state_file: str | Path | None) -> JsonStateStore | None:
    if state_file is None:
        return None
    return JsonStateStore(state_file)


def _require_platform_admin(actor_roles: Iterable[str]) -> None:
    if "platform_super_admin" not in actor_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Platform admin required")


def _tenant_id_from_tenant_path(path: str) -> str | None:
    parts = [part for part in path.split("/") if part]
    if len(parts) >= 3 and parts[0] == "v1" and parts[1] == "tenants":
        return parts[2]
    return None


def create_app(*, state_file: str | Path | None = None, legacy_write_mode: str | None = None) -> FastAPI:
    app = FastAPI(title="Store Platform API", version="0.1.0")
    state_store = _build_state_store(state_file)
    snapshot = state_store.load_snapshot() if state_store else None
    state = restore_state(snapshot) if snapshot else AppState()
    app.state.store_state = state
    app.state.state_store = state_store
    app.state.legacy_write_mode = resolve_legacy_write_mode(legacy_write_mode)

    def append_audit_log(
        *,
        action: str,
        entity_type: str,
        entity_id: str,
        tenant_id: str,
        actor_roles: list[str],
        branch_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        state.audit_logs.insert(
            0,
            {
                "id": _id(),
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "tenant_id": tenant_id,
                "branch_id": branch_id,
                "actor_roles": actor_roles,
                "details": details or {},
            },
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.middleware("http")
    async def persist_state_middleware(request, call_next):
        nonlocal state
        legacy_domain = classify_legacy_domain(request.url.path)
        legacy_write_mode_value = app.state.legacy_write_mode
        if legacy_domain and legacy_write_mode_value == "cutover" and request.method in MUTATION_METHODS:
            return build_cutover_block_response(domain=legacy_domain)

        if request.method != "POST" or state_store is None:
            response = await call_next(request)
            if legacy_domain:
                apply_legacy_authority_headers(
                    response,
                    domain=legacy_domain,
                    status_value="cutover" if legacy_write_mode_value == "cutover" else "deprecated",
                )
            return response

        if request.method == "POST":
            tenant_id = _tenant_id_from_tenant_path(request.url.path)
            if tenant_id and state.tenants.get(tenant_id, {}).get("status") == "SUSPENDED":
                return JSONResponse(status_code=status.HTTP_423_LOCKED, content={"detail": "Tenant is suspended"})

        state_before = deepcopy(state)
        response = await call_next(request)
        if legacy_domain:
            apply_legacy_authority_headers(
                response,
                domain=legacy_domain,
                status_value="cutover" if legacy_write_mode_value == "cutover" else "deprecated",
            )
        if response.status_code < 400:
            state_store.save_snapshot(snapshot_state(state))
        else:
            state = state_before
            app.state.store_state = state
        return response

    @app.post("/v1/platform/tenants")
    def create_tenant(payload: TenantCreate, actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_capability(actor_roles, "settings.manage")
        _require_platform_admin(actor_roles)
        tenant = {"id": _id(), "name": payload.name, "status": "ACTIVE", "suspension_reason": None}
        state.tenants[tenant["id"]] = tenant
        append_audit_log(
            action="tenant.created",
            entity_type="tenant",
            entity_id=tenant["id"],
            tenant_id=tenant["id"],
            actor_roles=actor_roles,
            details={"name": tenant["name"]},
        )
        return tenant

    @app.get("/v1/platform/tenants")
    def list_platform_tenants(actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_platform_admin(actor_roles)
        records = []
        for tenant in state.tenants.values():
            tenant_id = tenant["id"]
            branch_count = sum(1 for branch in state.branches.values() if branch["tenant_id"] == tenant_id)
            sales_invoice_total = sum(invoice["grand_total"] for invoice in state.invoices.values() if invoice["tenant_id"] == tenant_id)
            purchase_invoice_total = sum(invoice["grand_total"] for invoice in state.purchase_invoices.values() if invoice["tenant_id"] == tenant_id)
            records.append(
                build_platform_tenant_summary(
                    tenant=tenant,
                    branch_count=branch_count,
                    sales_invoice_total=sales_invoice_total,
                    purchase_invoice_total=purchase_invoice_total,
                )
            )
        return {"records": records}

    @app.get("/v1/platform/tenants/{tenant_id}/overview")
    def get_platform_tenant_overview(tenant_id: str, actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_platform_admin(actor_roles)
        tenant = state.tenants[tenant_id]
        branches = []
        for branch in state.branches.values():
            if branch["tenant_id"] != tenant_id:
                continue
            branch_invoices = [invoice for invoice in state.invoices.values() if invoice["tenant_id"] == tenant_id and invoice["branch_id"] == branch["id"]]
            branch_purchase_invoices = [
                invoice for invoice in state.purchase_invoices.values() if invoice["tenant_id"] == tenant_id and invoice["branch_id"] == branch["id"]
            ]
            branches.append(
                build_platform_branch_overview(
                    branch=branch,
                    sales_invoice_total=sum(invoice["grand_total"] for invoice in branch_invoices),
                    purchase_invoice_total=sum(invoice["grand_total"] for invoice in branch_purchase_invoices),
                    pending_irn_invoices=sum(1 for invoice in branch_invoices if invoice["irn_status"] == "IRN_PENDING"),
                )
            )
        return {
            "tenant": {
                "tenant_id": tenant["id"],
                "tenant_name": tenant["name"],
                "status": tenant.get("status", "ACTIVE"),
                "suspension_reason": tenant.get("suspension_reason"),
            },
            "branches": branches,
        }

    @app.post("/v1/platform/tenants/{tenant_id}/status")
    def update_tenant_status(
        tenant_id: str,
        payload: TenantStatusUpdate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "settings.manage")
        _require_platform_admin(actor_roles)
        tenant = state.tenants[tenant_id]
        tenant["status"] = payload.status
        tenant["suspension_reason"] = payload.reason if payload.status == "SUSPENDED" else None
        append_audit_log(
            action="tenant.status_changed",
            entity_type="tenant",
            entity_id=tenant_id,
            tenant_id=tenant_id,
            actor_roles=actor_roles,
            details={"status": tenant["status"], "suspension_reason": tenant["suspension_reason"]},
        )
        return tenant

    @app.post("/v1/platform/support-sessions")
    def create_platform_support_session(
        payload: SupportSessionCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "reports.view")
        _require_platform_admin(actor_roles)
        support_session = build_support_session(
            session_id=_id(),
            tenant_id=payload.tenant_id,
            branch_ids=payload.branch_ids,
        )
        state.support_sessions[support_session["id"]] = support_session
        append_audit_log(
            action="support_session.created",
            entity_type="support_session",
            entity_id=support_session["id"],
            tenant_id=payload.tenant_id,
            actor_roles=actor_roles,
            details={"branch_ids": payload.branch_ids, "access_mode": support_session["access_mode"]},
        )
        return support_session

    @app.get("/v1/platform/print-exceptions")
    def list_platform_print_exceptions(actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_platform_admin(actor_roles)
        return build_platform_print_exception_report(
            tenants_by_id=state.tenants,
            branches_by_id=state.branches,
            devices=list(state.devices.values()),
            print_jobs=list(state.print_jobs.values()),
        )

    @app.post("/v1/tenants/{tenant_id}/branches")
    def create_branch(tenant_id: str, payload: BranchCreate, actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_capability(actor_roles, "settings.manage")
        branch = {"id": _id(), "tenant_id": tenant_id, "name": payload.name, "gstin": payload.gstin}
        state.branches[branch["id"]] = branch
        append_audit_log(
            action="branch.created",
            entity_type="branch",
            entity_id=branch["id"],
            tenant_id=tenant_id,
            branch_id=branch["id"],
            actor_roles=actor_roles,
            details={"name": branch["name"]},
        )
        return branch

    @app.post("/v1/tenants/{tenant_id}/products")
    def create_product(tenant_id: str, payload: ProductCreate, actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_capability(actor_roles, "catalog.manage")
        product = payload.model_dump()
        product.update({"id": _id(), "tenant_id": tenant_id})
        state.products[product["id"]] = product
        append_audit_log(
            action="product.created",
            entity_type="product",
            entity_id=product["id"],
            tenant_id=tenant_id,
            actor_roles=actor_roles,
            details={"sku_code": product["sku_code"]},
        )
        return product

    @app.get("/v1/tenants/{tenant_id}/products")
    def list_products(tenant_id: str, actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_capability(actor_roles, "catalog.manage")
        return {"records": build_central_catalog_records(products=_list_tenant_products(state, tenant_id=tenant_id))}

    @app.post("/v1/tenants/{tenant_id}/barcode-allocations")
    def create_barcode_allocation(
        tenant_id: str,
        payload: BarcodeAllocationCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "barcode.manage")
        tenant = state.tenants[tenant_id]
        existing_barcode = normalize_barcode(payload.existing_barcode or "")
        barcode = allocate_barcode(
            tenant_name=tenant["name"],
            sku_code=payload.sku_code,
            existing=payload.existing_barcode,
        )
        source = "EXISTING" if existing_barcode else "ALLOCATED"
        append_audit_log(
            action="barcode.allocated",
            entity_type="barcode",
            entity_id=barcode,
            tenant_id=tenant_id,
            actor_roles=actor_roles,
            details={"sku_code": payload.sku_code, "source": source},
        )
        return {"barcode": barcode, "source": source}

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/catalog-overrides")
    def create_catalog_override(
        tenant_id: str,
        branch_id: str,
        payload: CatalogOverrideCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "pricing.manage")
        override = payload.model_dump()
        override.update({"id": _id(), "tenant_id": tenant_id, "branch_id": branch_id})
        state.catalog_overrides[_catalog_override_key(branch_id=branch_id, product_id=payload.product_id)] = override
        append_audit_log(
            action="catalog_override.saved",
            entity_type="catalog_override",
            entity_id=override["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"product_id": payload.product_id},
        )
        return override

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/catalog")
    def list_branch_catalog(
        tenant_id: str,
        branch_id: str,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("sales.bill", "reports.view"))
        return {"branch_id": branch_id, "records": _build_branch_catalog(state, tenant_id=tenant_id, branch_id=branch_id)}

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/barcode-lookup/{barcode}")
    def lookup_branch_barcode(
        tenant_id: str,
        branch_id: str,
        barcode: str,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "sales.bill")
        product = _find_product_by_barcode(state, tenant_id=tenant_id, barcode=barcode)
        override = state.catalog_overrides.get(_catalog_override_key(branch_id=branch_id, product_id=product["id"]))
        selling_price = override["selling_price"] if override and override.get("selling_price") is not None else product["selling_price"]
        return {
            "product_id": product["id"],
            "product_name": product["name"],
            "sku_code": product["sku_code"],
            "barcode": normalize_barcode(product["barcode"]),
            "selling_price": _money(selling_price),
            "stock_on_hand": _money(state.inventory.stock_on_hand(item_id=product["id"], branch_id=branch_id)),
            "is_active": True if override is None else override["is_active"],
        }

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/barcode-labels")
    def preview_branch_barcode_labels(
        tenant_id: str,
        branch_id: str,
        payload: BarcodeLabelPreviewCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "barcode.manage")
        product = state.products[payload.product_id]
        if product["tenant_id"] != tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        override = state.catalog_overrides.get(_catalog_override_key(branch_id=branch_id, product_id=payload.product_id))
        selling_price = override["selling_price"] if override and override.get("selling_price") is not None else product["selling_price"]
        label = build_barcode_label_model(
            sku_code=product["sku_code"],
            product_name=product["name"],
            barcode=product["barcode"],
            selling_price=selling_price,
        )
        labels = [dict(label) for _ in range(payload.copies)]
        append_audit_log(
            action="barcode_labels.previewed",
            entity_type="product",
            entity_id=product["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"copies": payload.copies},
        )
        return {"product_id": product["id"], "copies": payload.copies, "labels": labels}

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/reorder-rules")
    def save_reorder_rule(
        tenant_id: str,
        branch_id: str,
        payload: ReorderRuleCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "purchase.manage")
        if payload.target_stock < payload.min_stock:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target stock must be greater than or equal to minimum stock")
        rule = payload.model_dump()
        rule.update({"id": _id(), "tenant_id": tenant_id, "branch_id": branch_id})
        state.reorder_rules[_reorder_rule_key(branch_id=branch_id, product_id=payload.product_id)] = rule
        append_audit_log(
            action="reorder_rule.saved",
            entity_type="reorder_rule",
            entity_id=rule["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"product_id": payload.product_id, "min_stock": payload.min_stock, "target_stock": payload.target_stock},
        )
        return rule

    @app.post("/v1/tenants/{tenant_id}/suppliers")
    def create_supplier(tenant_id: str, payload: SupplierCreate, actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_capability(actor_roles, "purchase.manage")
        supplier = payload.model_dump()
        supplier.update({"id": _id(), "tenant_id": tenant_id})
        state.suppliers[supplier["id"]] = supplier
        append_audit_log(
            action="supplier.created",
            entity_type="supplier",
            entity_id=supplier["id"],
            tenant_id=tenant_id,
            actor_roles=actor_roles,
            details={"name": supplier["name"]},
        )
        return supplier

    @app.post("/v1/tenants/{tenant_id}/customers")
    def create_customer(tenant_id: str, payload: CustomerCreate, actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_capability(actor_roles, "sales.bill")
        customer = payload.model_dump()
        customer.update(
            {
                "id": _id(),
                "tenant_id": tenant_id,
                "visit_count": 0,
                "lifetime_value": 0.0,
                "last_sale_id": None,
            }
        )
        state.customers[customer["id"]] = customer
        append_audit_log(
            action="customer.created",
            entity_type="customer",
            entity_id=customer["id"],
            tenant_id=tenant_id,
            actor_roles=actor_roles,
            details={"name": customer["name"], "phone": customer["phone"]},
        )
        return customer

    @app.get("/v1/tenants/{tenant_id}/customers")
    def list_customers(
        tenant_id: str,
        query: str | None = None,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("sales.bill", "reports.view"))
        return {
            "records": build_customer_directory_records(
                customers=_list_tenant_customers(state, tenant_id=tenant_id),
                sales_by_id=state.sales,
                invoices_by_id=state.invoices,
                query=query,
            )
        }

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/customer-report")
    def get_branch_customer_report(
        tenant_id: str,
        branch_id: str,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "reports.view")
        return build_branch_customer_report(
            branch_id=branch_id,
            customers_by_id={customer["id"]: customer for customer in _list_tenant_customers(state, tenant_id=tenant_id)},
            sales=state.sales.values(),
            invoices_by_id=state.invoices,
            sale_returns=state.sale_returns.values(),
            credit_notes_by_id=state.credit_notes,
            exchange_orders=state.exchange_orders.values(),
        )

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-approval-report")
    def get_purchase_approval_report(
        tenant_id: str,
        branch_id: str,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("purchase.manage", "reports.view"))
        return build_purchase_approval_report(
            branch_id=branch_id,
            purchase_orders=[
                purchase_order for purchase_order in state.purchase_orders.values() if purchase_order["tenant_id"] == tenant_id
            ],
            suppliers_by_id={supplier["id"]: supplier for supplier in state.suppliers.values() if supplier["tenant_id"] == tenant_id},
            goods_receipts=[
                goods_receipt for goods_receipt in state.goods_receipts.values() if goods_receipt["tenant_id"] == tenant_id
            ],
        )

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/receiving-board")
    def get_receiving_board(
        tenant_id: str,
        branch_id: str,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("purchase.manage", "inventory.adjust", "reports.view"))
        return build_receiving_board(
            branch_id=branch_id,
            purchase_orders=[
                purchase_order for purchase_order in state.purchase_orders.values() if purchase_order["tenant_id"] == tenant_id
            ],
            suppliers_by_id={supplier["id"]: supplier for supplier in state.suppliers.values() if supplier["tenant_id"] == tenant_id},
            goods_receipts=[
                goods_receipt for goods_receipt in state.goods_receipts.values() if goods_receipt["tenant_id"] == tenant_id
            ],
        )

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/vendor-billing-board")
    def get_vendor_billing_board(
        tenant_id: str,
        branch_id: str,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("purchase.manage", "reports.view"))
        return build_vendor_billing_board(
            branch_id=branch_id,
            goods_receipts=[
                goods_receipt for goods_receipt in state.goods_receipts.values() if goods_receipt["tenant_id"] == tenant_id
            ],
            purchase_invoices=[
                purchase_invoice
                for purchase_invoice in state.purchase_invoices.values()
                if purchase_invoice["tenant_id"] == tenant_id
            ],
            suppliers_by_id={supplier["id"]: supplier for supplier in state.suppliers.values() if supplier["tenant_id"] == tenant_id},
        )

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/vendor-dispute-board")
    def get_vendor_dispute_board(
        tenant_id: str,
        branch_id: str,
        as_of_date: date | None = None,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("purchase.manage", "reports.view"))
        report_date = as_of_date or date.today()
        return build_vendor_dispute_board(
            branch_id=branch_id,
            as_of_date=report_date,
            vendor_disputes=[
                vendor_dispute for vendor_dispute in state.vendor_disputes.values() if vendor_dispute["tenant_id"] == tenant_id
            ],
            goods_receipts=[
                goods_receipt for goods_receipt in state.goods_receipts.values() if goods_receipt["tenant_id"] == tenant_id
            ],
            purchase_invoices=[
                purchase_invoice
                for purchase_invoice in state.purchase_invoices.values()
                if purchase_invoice["tenant_id"] == tenant_id
            ],
            suppliers_by_id={supplier["id"]: supplier for supplier in state.suppliers.values() if supplier["tenant_id"] == tenant_id},
        )

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/supplier-exception-report")
    def get_supplier_exception_report(
        tenant_id: str,
        branch_id: str,
        as_of_date: date | None = None,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("purchase.manage", "reports.view"))
        report_date = as_of_date or date.today()
        return build_supplier_exception_report(
            branch_id=branch_id,
            as_of_date=report_date,
            vendor_disputes=[
                vendor_dispute for vendor_dispute in state.vendor_disputes.values() if vendor_dispute["tenant_id"] == tenant_id
            ],
            goods_receipts=[
                goods_receipt for goods_receipt in state.goods_receipts.values() if goods_receipt["tenant_id"] == tenant_id
            ],
            purchase_invoices=[
                purchase_invoice
                for purchase_invoice in state.purchase_invoices.values()
                if purchase_invoice["tenant_id"] == tenant_id
            ],
            suppliers_by_id={supplier["id"]: supplier for supplier in state.suppliers.values() if supplier["tenant_id"] == tenant_id},
        )

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/supplier-performance-report")
    def get_supplier_performance_report(
        tenant_id: str,
        branch_id: str,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("purchase.manage", "reports.view"))
        return build_supplier_performance_report(
            branch_id=branch_id,
            purchase_orders=[
                purchase_order for purchase_order in state.purchase_orders.values() if purchase_order["tenant_id"] == tenant_id
            ],
            goods_receipts=[
                goods_receipt for goods_receipt in state.goods_receipts.values() if goods_receipt["tenant_id"] == tenant_id
            ],
            purchase_invoices=[
                purchase_invoice
                for purchase_invoice in state.purchase_invoices.values()
                if purchase_invoice["tenant_id"] == tenant_id
            ],
            supplier_returns=[
                supplier_return for supplier_return in state.supplier_returns.values() if supplier_return["tenant_id"] == tenant_id
            ],
            vendor_disputes=[
                vendor_dispute for vendor_dispute in state.vendor_disputes.values() if vendor_dispute["tenant_id"] == tenant_id
            ],
            suppliers_by_id={supplier["id"]: supplier for supplier in state.suppliers.values() if supplier["tenant_id"] == tenant_id},
        )

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/supplier-payables-report")
    def get_supplier_payables_report(
        tenant_id: str,
        branch_id: str,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("purchase.manage", "reports.view"))
        return build_supplier_payables_report(
            branch_id=branch_id,
            purchase_invoices=[
                purchase_invoice
                for purchase_invoice in state.purchase_invoices.values()
                if purchase_invoice["tenant_id"] == tenant_id
            ],
            supplier_returns=[
                supplier_return
                for supplier_return in state.supplier_returns.values()
                if supplier_return["tenant_id"] == tenant_id
            ],
            supplier_payments=[
                supplier_payment
                for supplier_payment in state.supplier_payments.values()
                if supplier_payment["tenant_id"] == tenant_id
            ],
            suppliers_by_id={supplier["id"]: supplier for supplier in state.suppliers.values() if supplier["tenant_id"] == tenant_id},
        )

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/supplier-aging-report")
    def get_supplier_aging_report(
        tenant_id: str,
        branch_id: str,
        as_of_date: date | None = None,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("purchase.manage", "reports.view"))
        report_date = as_of_date or date.today()
        return build_supplier_aging_report(
            branch_id=branch_id,
            as_of_date=report_date,
            purchase_invoices=[
                purchase_invoice
                for purchase_invoice in state.purchase_invoices.values()
                if purchase_invoice["tenant_id"] == tenant_id
            ],
            supplier_returns=[
                supplier_return
                for supplier_return in state.supplier_returns.values()
                if supplier_return["tenant_id"] == tenant_id
            ],
            supplier_payments=[
                supplier_payment
                for supplier_payment in state.supplier_payments.values()
                if supplier_payment["tenant_id"] == tenant_id
            ],
            suppliers_by_id={supplier["id"]: supplier for supplier in state.suppliers.values() if supplier["tenant_id"] == tenant_id},
        )

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/supplier-statements")
    def get_supplier_statement_report(
        tenant_id: str,
        branch_id: str,
        as_of_date: date | None = None,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("purchase.manage", "reports.view"))
        report_date = as_of_date or date.today()
        return build_supplier_statement_report(
            branch_id=branch_id,
            as_of_date=report_date,
            purchase_invoices=[
                purchase_invoice
                for purchase_invoice in state.purchase_invoices.values()
                if purchase_invoice["tenant_id"] == tenant_id
            ],
            supplier_returns=[
                supplier_return
                for supplier_return in state.supplier_returns.values()
                if supplier_return["tenant_id"] == tenant_id
            ],
            supplier_payments=[
                supplier_payment
                for supplier_payment in state.supplier_payments.values()
                if supplier_payment["tenant_id"] == tenant_id
            ],
            suppliers_by_id={supplier["id"]: supplier for supplier in state.suppliers.values() if supplier["tenant_id"] == tenant_id},
        )

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/supplier-due-schedule")
    def get_supplier_due_schedule(
        tenant_id: str,
        branch_id: str,
        as_of_date: date | None = None,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("purchase.manage", "reports.view"))
        report_date = as_of_date or date.today()
        return build_supplier_due_schedule(
            branch_id=branch_id,
            as_of_date=report_date,
            purchase_invoices=[
                purchase_invoice
                for purchase_invoice in state.purchase_invoices.values()
                if purchase_invoice["tenant_id"] == tenant_id
            ],
            supplier_returns=[
                supplier_return
                for supplier_return in state.supplier_returns.values()
                if supplier_return["tenant_id"] == tenant_id
            ],
            supplier_payments=[
                supplier_payment
                for supplier_payment in state.supplier_payments.values()
                if supplier_payment["tenant_id"] == tenant_id
            ],
            suppliers_by_id={supplier["id"]: supplier for supplier in state.suppliers.values() if supplier["tenant_id"] == tenant_id},
        )

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/supplier-payment-run")
    def get_supplier_payment_run(
        tenant_id: str,
        branch_id: str,
        as_of_date: date | None = None,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("purchase.manage", "reports.view"))
        report_date = as_of_date or date.today()
        return build_supplier_payment_run(
            branch_id=branch_id,
            as_of_date=report_date,
            purchase_invoices=[
                purchase_invoice
                for purchase_invoice in state.purchase_invoices.values()
                if purchase_invoice["tenant_id"] == tenant_id
            ],
            supplier_returns=[
                supplier_return
                for supplier_return in state.supplier_returns.values()
                if supplier_return["tenant_id"] == tenant_id
            ],
            supplier_payments=[
                supplier_payment
                for supplier_payment in state.supplier_payments.values()
                if supplier_payment["tenant_id"] == tenant_id
            ],
            suppliers_by_id={supplier["id"]: supplier for supplier in state.suppliers.values() if supplier["tenant_id"] == tenant_id},
        )

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/supplier-settlement-blockers")
    def get_supplier_settlement_blocker_report(
        tenant_id: str,
        branch_id: str,
        as_of_date: date | None = None,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("purchase.manage", "reports.view"))
        report_date = as_of_date or date.today()
        return build_supplier_settlement_blocker_report(
            branch_id=branch_id,
            as_of_date=report_date,
            purchase_invoices=[
                purchase_invoice
                for purchase_invoice in state.purchase_invoices.values()
                if purchase_invoice["tenant_id"] == tenant_id
            ],
            supplier_returns=[
                supplier_return
                for supplier_return in state.supplier_returns.values()
                if supplier_return["tenant_id"] == tenant_id
            ],
            supplier_payments=[
                supplier_payment
                for supplier_payment in state.supplier_payments.values()
                if supplier_payment["tenant_id"] == tenant_id
            ],
            vendor_disputes=[
                vendor_dispute for vendor_dispute in state.vendor_disputes.values() if vendor_dispute["tenant_id"] == tenant_id
            ],
            goods_receipts=[
                goods_receipt for goods_receipt in state.goods_receipts.values() if goods_receipt["tenant_id"] == tenant_id
            ],
            suppliers_by_id={supplier["id"]: supplier for supplier in state.suppliers.values() if supplier["tenant_id"] == tenant_id},
        )

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/supplier-escalation-report")
    def get_supplier_escalation_report(
        tenant_id: str,
        branch_id: str,
        as_of_date: date | None = None,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("purchase.manage", "reports.view"))
        report_date = as_of_date or date.today()
        return build_supplier_escalation_report(
            branch_id=branch_id,
            as_of_date=report_date,
            purchase_invoices=[
                purchase_invoice
                for purchase_invoice in state.purchase_invoices.values()
                if purchase_invoice["tenant_id"] == tenant_id
            ],
            supplier_returns=[
                supplier_return
                for supplier_return in state.supplier_returns.values()
                if supplier_return["tenant_id"] == tenant_id
            ],
            supplier_payments=[
                supplier_payment
                for supplier_payment in state.supplier_payments.values()
                if supplier_payment["tenant_id"] == tenant_id
            ],
            vendor_disputes=[
                vendor_dispute for vendor_dispute in state.vendor_disputes.values() if vendor_dispute["tenant_id"] == tenant_id
            ],
            goods_receipts=[
                goods_receipt for goods_receipt in state.goods_receipts.values() if goods_receipt["tenant_id"] == tenant_id
            ],
            suppliers_by_id={supplier["id"]: supplier for supplier in state.suppliers.values() if supplier["tenant_id"] == tenant_id},
        )

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/supplier-payment-register")
    def get_supplier_payment_register(
        tenant_id: str,
        branch_id: str,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("purchase.manage", "reports.view"))
        return build_supplier_payment_register(
            branch_id=branch_id,
            supplier_payments=[
                supplier_payment
                for supplier_payment in state.supplier_payments.values()
                if supplier_payment["tenant_id"] == tenant_id
            ],
            purchase_invoices=[
                purchase_invoice
                for purchase_invoice in state.purchase_invoices.values()
                if purchase_invoice["tenant_id"] == tenant_id
            ],
            supplier_returns=[
                supplier_return
                for supplier_return in state.supplier_returns.values()
                if supplier_return["tenant_id"] == tenant_id
            ],
            suppliers_by_id={supplier["id"]: supplier for supplier in state.suppliers.values() if supplier["tenant_id"] == tenant_id},
        )

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/supplier-payment-activity")
    def get_supplier_payment_activity(
        tenant_id: str,
        branch_id: str,
        as_of_date: date | None = None,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("purchase.manage", "reports.view"))
        report_date = as_of_date or date.today()
        return build_supplier_payment_activity_report(
            branch_id=branch_id,
            as_of_date=report_date,
            supplier_payments=[
                supplier_payment
                for supplier_payment in state.supplier_payments.values()
                if supplier_payment["tenant_id"] == tenant_id
            ],
            purchase_invoices=[
                purchase_invoice
                for purchase_invoice in state.purchase_invoices.values()
                if purchase_invoice["tenant_id"] == tenant_id
            ],
            supplier_returns=[
                supplier_return
                for supplier_return in state.supplier_returns.values()
                if supplier_return["tenant_id"] == tenant_id
            ],
            suppliers_by_id={supplier["id"]: supplier for supplier in state.suppliers.values() if supplier["tenant_id"] == tenant_id},
        )

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/supplier-settlement-report")
    def get_supplier_settlement_report(
        tenant_id: str,
        branch_id: str,
        as_of_date: date | None = None,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("purchase.manage", "reports.view"))
        report_date = as_of_date or date.today()
        return build_supplier_settlement_report(
            branch_id=branch_id,
            as_of_date=report_date,
            purchase_invoices=[
                purchase_invoice
                for purchase_invoice in state.purchase_invoices.values()
                if purchase_invoice["tenant_id"] == tenant_id
            ],
            supplier_returns=[
                supplier_return
                for supplier_return in state.supplier_returns.values()
                if supplier_return["tenant_id"] == tenant_id
            ],
            supplier_payments=[
                supplier_payment
                for supplier_payment in state.supplier_payments.values()
                if supplier_payment["tenant_id"] == tenant_id
            ],
            suppliers_by_id={supplier["id"]: supplier for supplier in state.suppliers.values() if supplier["tenant_id"] == tenant_id},
        )

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/cash-sessions/open")
    def open_cash_session(
        tenant_id: str,
        branch_id: str,
        payload: CashSessionOpenCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "sales.bill")
        cash_session = {
            "id": _id(),
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "status": "OPEN",
            "opening_float": _money(payload.opening_float),
            "cash_sales_total": 0.0,
            "expected_close_amount": _money(payload.opening_float),
            "closing_amount": None,
            "variance_amount": None,
        }
        state.cash_sessions[cash_session["id"]] = cash_session
        append_audit_log(
            action="cash_session.opened",
            entity_type="cash_session",
            entity_id=cash_session["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"opening_float": cash_session["opening_float"]},
        )
        return cash_session

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/cash-sessions/{cash_session_id}/close")
    def close_cash_session(
        tenant_id: str,
        branch_id: str,
        cash_session_id: str,
        payload: CashSessionCloseCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "sales.bill")
        cash_session = state.cash_sessions[cash_session_id]
        if cash_session["status"] != "OPEN":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cash session already closed")
        close_summary = compute_cash_session_close(
            opening_float=cash_session["opening_float"],
            cash_sales_total=cash_session["cash_sales_total"],
            closing_amount=payload.closing_amount,
        )
        cash_session.update(
            {
                "status": "CLOSED",
                "closing_amount": _money(payload.closing_amount),
                "expected_close_amount": close_summary["expected_close_amount"],
                "variance_amount": close_summary["variance_amount"],
            }
        )
        append_audit_log(
            action="cash_session.closed",
            entity_type="cash_session",
            entity_id=cash_session_id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"variance_amount": cash_session["variance_amount"]},
        )
        return cash_session

    @app.get("/v1/tenants/{tenant_id}/customers/{customer_id}")
    def get_customer(tenant_id: str, customer_id: str, actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("sales.bill", "reports.view"))
        return _find_customer(state, tenant_id=tenant_id, customer_id=customer_id)

    @app.get("/v1/tenants/{tenant_id}/customers/{customer_id}/history")
    def get_customer_history(tenant_id: str, customer_id: str, actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("sales.bill", "reports.view"))
        return build_customer_history_report(
            customer=_find_customer(state, tenant_id=tenant_id, customer_id=customer_id),
            sales=state.sales.values(),
            invoices_by_id=state.invoices,
            sale_returns=state.sale_returns.values(),
            credit_notes_by_id=state.credit_notes,
            exchange_orders=state.exchange_orders.values(),
        )

    @app.post("/v1/tenants/{tenant_id}/staff-assignments")
    def create_staff_assignment(
        tenant_id: str,
        payload: StaffAssignmentCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "staff.manage")
        assignment = payload.model_dump()
        assignment.update({"id": _id(), "tenant_id": tenant_id})
        state.staff_assignments[assignment["id"]] = assignment
        append_audit_log(
            action="staff_assignment.created",
            entity_type="staff_assignment",
            entity_id=assignment["id"],
            tenant_id=tenant_id,
            branch_id=assignment["branch_id"],
            actor_roles=actor_roles,
            details={"role": assignment["role"]},
        )
        return assignment

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/devices")
    def register_device(
        tenant_id: str,
        branch_id: str,
        payload: DeviceRegistrationCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "staff.manage")
        device = payload.model_dump()
        device.update({"id": _id(), "tenant_id": tenant_id, "branch_id": branch_id})
        state.devices[device["id"]] = device
        append_audit_log(
            action="device.registered",
            entity_type="device",
            entity_id=device["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"session_surface": device["session_surface"]},
        )
        return device

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/print-jobs/invoices")
    def queue_invoice_print_job(
        tenant_id: str,
        branch_id: str,
        payload: InvoicePrintJobCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "sales.bill")
        _require_branch_device(state, tenant_id=tenant_id, branch_id=branch_id, device_id=payload.device_id)
        invoice = state.invoices.get(payload.invoice_id)
        if not invoice or invoice["tenant_id"] != tenant_id or invoice["branch_id"] != branch_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        receipt_lines = build_invoice_receipt_lines(
            invoice_number=invoice["invoice_number"],
            customer_name=invoice["customer_name"],
            customer_gstin=invoice.get("customer_gstin"),
            items=[
                {
                    "name": state.products[line["product_id"]]["name"],
                    "qty": line["quantity"],
                    "unit_price": line["unit_price"],
                    "line_total": line["line_total"],
                }
                for line in invoice["lines"]
            ],
            totals={
                "subtotal": invoice["subtotal"],
                "cgst": invoice["tax"]["cgst"],
                "sgst": invoice["tax"]["sgst"],
                "igst": invoice["tax"]["igst"],
                "grand_total": invoice["grand_total"],
            },
            irn_status=invoice["irn_status"],
        )
        print_job = build_print_job(
            job_id=_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=payload.device_id,
            job_type="SALES_INVOICE",
            copies=payload.copies,
            payload={
                "invoice_id": invoice["id"],
                "invoice_number": invoice["invoice_number"],
                "receipt_lines": receipt_lines,
            },
            actor_roles=actor_roles,
        )
        state.print_jobs[print_job["id"]] = print_job
        append_audit_log(
            action="print_job.created",
            entity_type="print_job",
            entity_id=print_job["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"job_type": print_job["job_type"], "device_id": payload.device_id},
        )
        return print_job

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/print-jobs/barcode-labels")
    def queue_barcode_label_print_job(
        tenant_id: str,
        branch_id: str,
        payload: BarcodePrintJobCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "barcode.manage")
        _require_branch_device(state, tenant_id=tenant_id, branch_id=branch_id, device_id=payload.device_id)
        product = state.products.get(payload.product_id)
        if not product or product["tenant_id"] != tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        override = state.catalog_overrides.get(_catalog_override_key(branch_id=branch_id, product_id=payload.product_id))
        selling_price = override["selling_price"] if override and override.get("selling_price") is not None else product["selling_price"]
        labels = [
            build_barcode_label_model(
                sku_code=product["sku_code"],
                product_name=product["name"],
                barcode=product["barcode"],
                selling_price=selling_price,
            )
            for _ in range(payload.copies)
        ]
        print_job = build_print_job(
            job_id=_id(),
            tenant_id=tenant_id,
            branch_id=branch_id,
            device_id=payload.device_id,
            job_type="BARCODE_LABEL",
            copies=payload.copies,
            payload={"product_id": product["id"], "labels": labels},
            actor_roles=actor_roles,
        )
        state.print_jobs[print_job["id"]] = print_job
        append_audit_log(
            action="print_job.created",
            entity_type="print_job",
            entity_id=print_job["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"job_type": print_job["job_type"], "device_id": payload.device_id},
        )
        return print_job

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/print-health-report")
    def branch_print_health_report(tenant_id: str, branch_id: str, actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_capability(actor_roles, "reports.view")
        branch_devices = [
            device for device in state.devices.values() if device["tenant_id"] == tenant_id and device["branch_id"] == branch_id
        ]
        branch_print_jobs = [
            job for job in state.print_jobs.values() if job["tenant_id"] == tenant_id and job["branch_id"] == branch_id
        ]
        return {
            "branch_id": branch_id,
            **build_branch_print_health_report(devices=branch_devices, print_jobs=branch_print_jobs),
        }

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/devices/{device_id}/print-jobs")
    def list_device_print_jobs(
        tenant_id: str,
        branch_id: str,
        device_id: str,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "sales.bill")
        _require_branch_device(state, tenant_id=tenant_id, branch_id=branch_id, device_id=device_id)
        records = [
            job
            for job in state.print_jobs.values()
            if job["tenant_id"] == tenant_id and job["branch_id"] == branch_id and job["device_id"] == device_id and job["status"] == "QUEUED"
        ]
        return {"device_id": device_id, "records": records}

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/devices/{device_id}/print-jobs/{job_id}/complete")
    def complete_device_print_job(
        tenant_id: str,
        branch_id: str,
        device_id: str,
        job_id: str,
        payload: PrintJobCompletionInput,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "sales.bill")
        _require_branch_device(state, tenant_id=tenant_id, branch_id=branch_id, device_id=device_id)
        job = state.print_jobs.get(job_id)
        if not job or job["tenant_id"] != tenant_id or job["branch_id"] != branch_id or job["device_id"] != device_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Print job not found")
        complete_print_job(job=job, status=payload.status, failure_reason=payload.failure_reason)
        append_audit_log(
            action="print_job.completed",
            entity_type="print_job",
            entity_id=job["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"status": payload.status, "device_id": device_id},
        )
        return job

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders")
    def create_purchase_order(
        tenant_id: str,
        branch_id: str,
        payload: PurchaseOrderCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "purchase.manage")
        purchase_order = {
            "id": _id(),
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "supplier_id": payload.supplier_id,
            "lines": [line.model_dump() for line in payload.lines],
            "approval_status": "NOT_REQUESTED",
            "approval_requested_note": None,
            "approval_requested_by_roles": None,
            "approval_decision_note": None,
            "approval_decided_by_roles": None,
        }
        state.purchase_orders[purchase_order["id"]] = purchase_order
        append_audit_log(
            action="purchase_order.created",
            entity_type="purchase_order",
            entity_id=purchase_order["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"line_count": len(purchase_order["lines"])},
        )
        return purchase_order

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/submit-approval")
    def submit_purchase_order_approval(
        tenant_id: str,
        branch_id: str,
        purchase_order_id: str,
        payload: PurchaseOrderDecisionInput,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "purchase.manage")
        purchase_order = _find_purchase_order(state, tenant_id=tenant_id, branch_id=branch_id, purchase_order_id=purchase_order_id)
        try:
            request_purchase_order_approval(
                purchase_order=purchase_order,
                note=payload.note,
                actor_roles=actor_roles,
                requested_on=date.today().isoformat(),
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        append_audit_log(
            action="purchase_order.approval_requested",
            entity_type="purchase_order",
            entity_id=purchase_order_id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"note": payload.note} if payload.note else {},
        )
        return purchase_order

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/approve")
    def approve_purchase_order(
        tenant_id: str,
        branch_id: str,
        purchase_order_id: str,
        payload: PurchaseOrderDecisionInput,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "purchase.manage")
        purchase_order = _find_purchase_order(state, tenant_id=tenant_id, branch_id=branch_id, purchase_order_id=purchase_order_id)
        try:
            decide_purchase_order_approval(
                purchase_order=purchase_order,
                decision="APPROVED",
                note=payload.note,
                actor_roles=actor_roles,
                decided_on=date.today().isoformat(),
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        append_audit_log(
            action="purchase_order.approved",
            entity_type="purchase_order",
            entity_id=purchase_order_id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"note": payload.note} if payload.note else {},
        )
        return purchase_order

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/reject")
    def reject_purchase_order(
        tenant_id: str,
        branch_id: str,
        purchase_order_id: str,
        payload: PurchaseOrderDecisionInput,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "purchase.manage")
        purchase_order = _find_purchase_order(state, tenant_id=tenant_id, branch_id=branch_id, purchase_order_id=purchase_order_id)
        try:
            decide_purchase_order_approval(
                purchase_order=purchase_order,
                decision="REJECTED",
                note=payload.note,
                actor_roles=actor_roles,
                decided_on=date.today().isoformat(),
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        append_audit_log(
            action="purchase_order.rejected",
            entity_type="purchase_order",
            entity_id=purchase_order_id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"note": payload.note} if payload.note else {},
        )
        return purchase_order

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts")
    def create_goods_receipt(
        tenant_id: str,
        branch_id: str,
        payload: GoodsReceiptCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "inventory.adjust")
        purchase_order = _find_purchase_order(state, tenant_id=tenant_id, branch_id=branch_id, purchase_order_id=payload.purchase_order_id)
        try:
            ensure_goods_receipt_not_already_created(
                purchase_order_id=payload.purchase_order_id,
                goods_receipts=state.goods_receipts.values(),
            )
            ensure_purchase_order_receivable(purchase_order=purchase_order)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        for line in purchase_order["lines"]:
            state.inventory.post_entry(
                item_id=line["product_id"],
                branch_id=branch_id,
                quantity=line["quantity"],
                entry_type="PURCHASE_RECEIPT",
            )
        receipt = {
            "id": _id(),
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "purchase_order_id": payload.purchase_order_id,
            "supplier_id": purchase_order["supplier_id"],
            "received_on": date.today().isoformat(),
            "lines": [dict(line) for line in purchase_order["lines"]],
        }
        state.goods_receipts[receipt["id"]] = receipt
        append_audit_log(
            action="goods_receipt.created",
            entity_type="goods_receipt",
            entity_id=receipt["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"purchase_order_id": payload.purchase_order_id},
        )
        return receipt

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts/{goods_receipt_id}/batch-lots")
    def create_goods_receipt_batch_lots(
        tenant_id: str,
        branch_id: str,
        goods_receipt_id: str,
        payload: GoodsReceiptBatchCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "inventory.adjust")
        goods_receipt = state.goods_receipts.get(goods_receipt_id)
        if not goods_receipt or goods_receipt["tenant_id"] != tenant_id or goods_receipt["branch_id"] != branch_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goods receipt not found")
        if any(lot["goods_receipt_id"] == goods_receipt_id for lot in state.batch_lots.values()):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Batch lots already recorded for goods receipt")

        lot_inputs = [lot.model_dump() for lot in payload.lots]
        try:
            validate_goods_receipt_batch_lots(goods_receipt["lines"], lot_inputs)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        records = []
        for lot_input in lot_inputs:
            record = {
                "id": _id(),
                "tenant_id": tenant_id,
                "branch_id": branch_id,
                "goods_receipt_id": goods_receipt_id,
                "purchase_order_id": goods_receipt["purchase_order_id"],
                "product_id": lot_input["product_id"],
                "batch_number": lot_input["batch_number"],
                "quantity": _money(lot_input["quantity"]),
                "written_off_quantity": 0.0,
                "expiry_date": lot_input["expiry_date"],
            }
            state.batch_lots[record["id"]] = record
            records.append(record)

        append_audit_log(
            action="batch_lots.recorded",
            entity_type="goods_receipt",
            entity_id=goods_receipt_id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"batch_lot_count": len(records)},
        )
        return {"goods_receipt_id": goods_receipt_id, "records": records}

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-invoices")
    def create_purchase_invoice(
        tenant_id: str,
        branch_id: str,
        payload: PurchaseInvoiceCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "purchase.manage")
        goods_receipt = state.goods_receipts[payload.goods_receipt_id]
        try:
            ensure_purchase_invoice_not_already_created(
                goods_receipt_id=goods_receipt["id"],
                purchase_invoices=state.purchase_invoices.values(),
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        supplier = state.suppliers[goods_receipt["supplier_id"]]
        branch = state.branches[branch_id]
        invoice_lines: list[dict[str, Any]] = []
        line_inputs: list[dict[str, float]] = []
        for line in goods_receipt["lines"]:
            product = state.products[line["product_id"]]
            line_inputs.append(
                {
                    "quantity": float(line["quantity"]),
                    "unit_cost": float(line["unit_cost"]),
                    "tax_rate_percent": float(product["tax_rate_percent"]),
                }
            )
            invoice_lines.append(
                {
                    "product_id": line["product_id"],
                    "quantity": line["quantity"],
                    "unit_cost": line["unit_cost"],
                    "line_total": _money(line["quantity"] * line["unit_cost"]),
                }
            )
        totals = compute_purchase_totals(
            seller_gstin=supplier.get("gstin"),
            buyer_gstin=branch.get("gstin"),
            lines=line_inputs,
        )
        invoice_date = date.today()
        payment_terms_days = int(supplier.get("payment_terms_days", 0) or 0)
        due_date = compute_supplier_due_date(invoice_date=invoice_date, payment_terms_days=payment_terms_days)
        purchase_invoice = {
            "id": _id(),
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "goods_receipt_id": goods_receipt["id"],
            "purchase_order_id": goods_receipt["purchase_order_id"],
            "supplier_id": goods_receipt["supplier_id"],
            "invoice_date": invoice_date.isoformat(),
            "due_date": due_date.isoformat(),
            "payment_terms_days": payment_terms_days,
            "invoice_number": next_purchase_invoice_number(state.invoice_sequences, branch_id=branch_id, fiscal_year="2526"),
            "subtotal": totals["subtotal"],
            "tax": totals["tax"],
            "grand_total": totals["grand_total"],
            "lines": invoice_lines,
        }
        state.purchase_invoices[purchase_invoice["id"]] = purchase_invoice
        append_audit_log(
            action="purchase_invoice.created",
            entity_type="purchase_invoice",
            entity_id=purchase_invoice["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"invoice_number": purchase_invoice["invoice_number"], "goods_receipt_id": goods_receipt["id"]},
        )
        return purchase_invoice

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/vendor-disputes")
    def create_vendor_dispute(
        tenant_id: str,
        branch_id: str,
        payload: VendorDisputeCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "purchase.manage")
        if bool(payload.goods_receipt_id) == bool(payload.purchase_invoice_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exactly one of goods_receipt_id or purchase_invoice_id is required",
            )

        goods_receipt_id = payload.goods_receipt_id
        purchase_invoice_id = payload.purchase_invoice_id
        if goods_receipt_id:
            goods_receipt = _find_goods_receipt(
                state,
                tenant_id=tenant_id,
                branch_id=branch_id,
                goods_receipt_id=goods_receipt_id,
            )
            supplier_id = goods_receipt["supplier_id"]
        else:
            purchase_invoice = _find_purchase_invoice(
                state,
                tenant_id=tenant_id,
                branch_id=branch_id,
                purchase_invoice_id=purchase_invoice_id or "",
            )
            supplier_id = purchase_invoice["supplier_id"]

        vendor_dispute = {
            "id": _id(),
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "supplier_id": supplier_id,
            "goods_receipt_id": goods_receipt_id,
            "purchase_invoice_id": purchase_invoice_id,
            "dispute_type": payload.dispute_type,
            "note": payload.note,
            "status": "OPEN",
            "opened_on": date.today().isoformat(),
            "resolved_on": None,
            "resolution_note": None,
        }
        state.vendor_disputes[vendor_dispute["id"]] = vendor_dispute
        append_audit_log(
            action="vendor_dispute.created",
            entity_type="vendor_dispute",
            entity_id=vendor_dispute["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={
                "goods_receipt_id": goods_receipt_id,
                "purchase_invoice_id": purchase_invoice_id,
                "dispute_type": payload.dispute_type,
            },
        )
        return vendor_dispute

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/vendor-disputes/{dispute_id}/resolve")
    def resolve_vendor_dispute(
        tenant_id: str,
        branch_id: str,
        dispute_id: str,
        payload: VendorDisputeResolve,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "purchase.manage")
        vendor_dispute = state.vendor_disputes.get(dispute_id)
        if not vendor_dispute or vendor_dispute["tenant_id"] != tenant_id or vendor_dispute["branch_id"] != branch_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor dispute not found")
        if vendor_dispute["status"] == "RESOLVED":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vendor dispute already resolved")

        vendor_dispute["status"] = "RESOLVED"
        vendor_dispute["resolved_on"] = date.today().isoformat()
        vendor_dispute["resolution_note"] = payload.resolution_note
        append_audit_log(
            action="vendor_dispute.resolved",
            entity_type="vendor_dispute",
            entity_id=vendor_dispute["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"resolution_note": payload.resolution_note},
        )
        return vendor_dispute

    @app.post("/v1/tenants/{tenant_id}/transfers")
    def create_transfer(
        tenant_id: str,
        payload: TransferCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "inventory.transfer")
        transfer = {
            "id": _id(),
            "tenant_id": tenant_id,
            "source_branch_id": payload.source_branch_id,
            "destination_branch_id": payload.destination_branch_id,
            "lines": [
                state.inventory.transfer_stock(
                    item_id=line.product_id,
                    source_branch_id=payload.source_branch_id,
                    destination_branch_id=payload.destination_branch_id,
                    quantity=line.quantity,
                )
                for line in payload.lines
            ],
        }
        state.transfers[transfer["id"]] = transfer
        append_audit_log(
            action="transfer.created",
            entity_type="transfer",
            entity_id=transfer["id"],
            tenant_id=tenant_id,
            branch_id=payload.source_branch_id,
            actor_roles=actor_roles,
            details={"destination_branch_id": payload.destination_branch_id, "line_count": len(transfer["lines"])},
        )
        return transfer

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/sales")
    def create_sale(
        tenant_id: str,
        branch_id: str,
        payload: SaleCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "sales.bill")
        branch = state.branches[branch_id]
        customer = state.customers.get(payload.customer_id) if payload.customer_id else None
        if payload.customer_id and not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        subtotal = 0.0
        hsn_sac_code = None
        line_items: list[dict[str, Any]] = []
        for line in payload.lines:
            product, unit_price = _resolve_branch_pricing(state, branch_id=branch_id, product_id=line.product_id)
            line_total = _money(unit_price * line.quantity)
            subtotal += line_total
            hsn_sac_code = hsn_sac_code or product["hsn_sac_code"]
            line_items.append(
                {
                    "product_id": line.product_id,
                    "quantity": line.quantity,
                    "unit_price": unit_price,
                    "line_total": line_total,
                }
            )
            state.inventory.post_entry(
                item_id=line.product_id,
                branch_id=branch_id,
                quantity=-line.quantity,
                entry_type="SALE",
            )

        tax = calculate_invoice_taxes(
            seller_gstin=branch.get("gstin"),
            buyer_gstin=payload.customer_gstin,
            taxable_total=_money(subtotal),
            tax_rate_percent=state.products[payload.lines[0].product_id]["tax_rate_percent"],
        )
        grand_total = _money(subtotal + tax["tax_total"])
        invoice = {
            "id": _id(),
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "invoice_number": next_invoice_number(state.invoice_sequences, branch_id=branch_id, fiscal_year="2526"),
            "customer_name": payload.customer_name,
            "customer_gstin": payload.customer_gstin,
            "hsn_sac_code": hsn_sac_code,
            "subtotal": _money(subtotal),
            "tax": tax,
            "grand_total": grand_total,
            "irn_status": "NOT_REQUIRED" if not payload.customer_gstin else "IRN_PENDING",
            "lines": line_items,
        }
        sale = {
            "id": _id(),
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "invoice_id": invoice["id"],
            "customer_id": payload.customer_id,
            "payment_method": payload.payment_method,
            "cash_session_id": payload.cash_session_id,
            "payment_amount": payload.payment_amount,
            "lines": line_items,
        }
        state.invoices[invoice["id"]] = invoice
        state.sales[sale["id"]] = sale
        if payload.cash_session_id:
            cash_session = state.cash_sessions[payload.cash_session_id]
            if cash_session["status"] != "OPEN":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cash session not open")
            if payload.payment_method == "cash":
                cash_session["cash_sales_total"] = _money(cash_session["cash_sales_total"] + grand_total)
                cash_session["expected_close_amount"] = _money(cash_session["opening_float"] + cash_session["cash_sales_total"])
        if customer:
            customer["visit_count"] += 1
            customer["lifetime_value"] = _money(customer["lifetime_value"] + grand_total)
            customer["last_sale_id"] = sale["id"]
            if payload.customer_gstin and not customer.get("gstin"):
                customer["gstin"] = payload.customer_gstin
        append_audit_log(
            action="sale.created",
            entity_type="sale",
            entity_id=sale["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"invoice_id": invoice["id"], "grand_total": grand_total},
        )
        return {"sale_id": sale["id"], "invoice": invoice}

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/stock-counts")
    def create_stock_count(
        tenant_id: str,
        branch_id: str,
        payload: StockCountCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "inventory.adjust")
        stock_count = {
            "id": _id(),
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "reason": payload.reason,
            "lines": [
                state.inventory.apply_stock_count(
                    item_id=line.product_id,
                    branch_id=branch_id,
                    counted_quantity=line.counted_quantity,
                )
                for line in payload.lines
            ],
        }
        state.stock_counts[stock_count["id"]] = stock_count
        append_audit_log(
            action="stock_count.created",
            entity_type="stock_count",
            entity_id=stock_count["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"line_count": len(stock_count["lines"]), "reason": payload.reason},
        )
        return stock_count

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/dashboard")
    def branch_dashboard(tenant_id: str, branch_id: str, actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_capability(actor_roles, "reports.view")
        branch_invoices = [invoice for invoice in state.invoices.values() if invoice["tenant_id"] == tenant_id and invoice["branch_id"] == branch_id]
        low_stock_products = []
        for product in state.products.values():
            if product["tenant_id"] != tenant_id:
                continue
            stock_on_hand = state.inventory.stock_on_hand(item_id=product["id"], branch_id=branch_id)
            if 0 < stock_on_hand <= 5:
                low_stock_products.append(
                    {
                        "product_id": product["id"],
                        "product_name": product["name"],
                        "stock_on_hand": stock_on_hand,
                    }
                )
        return {
            "branch_id": branch_id,
            "sales_count": len(branch_invoices),
            "gross_sales_total": _money(sum(invoice["grand_total"] for invoice in branch_invoices)),
            "pending_irn_invoices": sum(1 for invoice in branch_invoices if invoice["irn_status"] == "IRN_PENDING"),
            "customer_count": sum(1 for customer in state.customers.values() if customer["tenant_id"] == tenant_id),
            "low_stock_products": low_stock_products,
        }

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/inventory-snapshot")
    def branch_inventory_snapshot(tenant_id: str, branch_id: str, actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_any_capability(actor_roles, ("reports.view", "inventory.adjust"))
        return {
            "branch_id": branch_id,
            **build_inventory_snapshot_report(catalog_records=_build_branch_catalog(state, tenant_id=tenant_id, branch_id=branch_id)),
        }

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/commercial-report")
    def branch_commercial_report(tenant_id: str, branch_id: str, actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_capability(actor_roles, "reports.view")
        branch_invoices = [invoice for invoice in state.invoices.values() if invoice["tenant_id"] == tenant_id and invoice["branch_id"] == branch_id]
        branch_sales = [sale for sale in state.sales.values() if sale["tenant_id"] == tenant_id and sale["branch_id"] == branch_id]
        branch_credit_notes = [note for note in state.credit_notes.values() if note["tenant_id"] == tenant_id and note["branch_id"] == branch_id]
        products_by_id = {product["id"]: product for product in state.products.values() if product["tenant_id"] == tenant_id}
        stock_rows = [
            {
                "product_id": product["id"],
                "product_name": product["name"],
                "stock_on_hand": state.inventory.stock_on_hand(item_id=product["id"], branch_id=branch_id),
            }
            for product in products_by_id.values()
        ]
        return {
            "branch_id": branch_id,
            "sales_summary": build_sales_summary(invoices=branch_invoices, credit_notes=branch_credit_notes),
            "payment_mix": build_payment_mix(sales=branch_sales, invoices_by_id=state.invoices),
            "top_products": build_top_products(invoices=branch_invoices, products_by_id=products_by_id),
            "stock_risk": build_stock_risk_report(stock_rows=stock_rows),
        }

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/replenishment-report")
    def branch_replenishment_report(tenant_id: str, branch_id: str, actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_capability(actor_roles, "reports.view")
        branch_rules = [rule for rule in state.reorder_rules.values() if rule["tenant_id"] == tenant_id and rule["branch_id"] == branch_id]
        products_by_id = {product["id"]: product for product in state.products.values() if product["tenant_id"] == tenant_id}
        stock_by_product = {
            product_id: state.inventory.stock_on_hand(item_id=product_id, branch_id=branch_id)
            for product_id in products_by_id
        }
        records = build_replenishment_records(
            reorder_rules=branch_rules,
            products_by_id=products_by_id,
            stock_by_product=stock_by_product,
        )
        return {
            "branch_id": branch_id,
            "rule_count": len(branch_rules),
            "reorder_now_count": sum(1 for record in records if record["status"] == "REORDER_NOW"),
            "watch_count": sum(1 for record in records if record["status"] == "WATCH"),
            "records": [record for record in records if record["status"] != "OK"],
        }

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/batch-expiry-report")
    def branch_batch_expiry_report(tenant_id: str, branch_id: str, actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_capability(actor_roles, "reports.view")
        return {"branch_id": branch_id, **_build_branch_batch_report(state, tenant_id=tenant_id, branch_id=branch_id)}

    @app.get("/v1/tenants/{tenant_id}/branches/{branch_id}/finance-history")
    def branch_finance_history(tenant_id: str, branch_id: str, actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_capability(actor_roles, "reports.view")
        sales_invoices = [invoice for invoice in state.invoices.values() if invoice["tenant_id"] == tenant_id and invoice["branch_id"] == branch_id]
        purchase_invoices = [invoice for invoice in state.purchase_invoices.values() if invoice["tenant_id"] == tenant_id and invoice["branch_id"] == branch_id]
        customer_credit_notes = [note for note in state.credit_notes.values() if note["tenant_id"] == tenant_id and note["branch_id"] == branch_id]
        supplier_credit_notes = [note for note in state.supplier_returns.values() if note["tenant_id"] == tenant_id and note["branch_id"] == branch_id]
        cash_sessions = [session for session in state.cash_sessions.values() if session["tenant_id"] == tenant_id and session["branch_id"] == branch_id]
        recent_documents = [
            *[
                {"document_type": "sales_invoice", "document_number": invoice["invoice_number"], "grand_total": invoice["grand_total"]}
                for invoice in sales_invoices
            ],
            *[
                {"document_type": "purchase_invoice", "document_number": invoice["invoice_number"], "grand_total": invoice["grand_total"]}
                for invoice in purchase_invoices
            ],
            *[
                {
                    "document_type": "customer_credit_note",
                    "document_number": note["credit_note_number"],
                    "grand_total": note["grand_total"],
                }
                for note in customer_credit_notes
            ],
            *[
                {
                    "document_type": "supplier_credit_note",
                    "document_number": note["supplier_credit_note_number"],
                    "grand_total": note["grand_total"],
                }
                for note in supplier_credit_notes
            ],
        ]
        return {
            "branch_id": branch_id,
            "sales_invoice_total": _money(sum(invoice["grand_total"] for invoice in sales_invoices)),
            "purchase_invoice_total": _money(sum(invoice["grand_total"] for invoice in purchase_invoices)),
            "customer_credit_note_total": _money(sum(note["grand_total"] for note in customer_credit_notes)),
            "supplier_credit_note_total": _money(sum(note["grand_total"] for note in supplier_credit_notes)),
            "cash_variance_total": _money(sum(session["variance_amount"] or 0 for session in cash_sessions)),
            "recent_documents": recent_documents[-5:],
        }

    @app.get("/v1/tenants/{tenant_id}/audit-logs")
    def list_audit_logs(tenant_id: str, actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_capability(actor_roles, "reports.view")
        return {"records": [entry for entry in state.audit_logs if entry["tenant_id"] == tenant_id]}

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/compliance/gst-exports")
    def create_gst_export(
        tenant_id: str,
        branch_id: str,
        payload: GExportCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "compliance.export")
        invoice = state.invoices[payload.invoice_id]
        branch = state.branches[branch_id]
        export_job = prepare_gst_export_job(
            invoice_id=invoice["id"],
            invoice_number=invoice["invoice_number"],
            seller_gstin=branch.get("gstin") or "",
            buyer_gstin=invoice.get("customer_gstin"),
            hsn_sac_code=invoice.get("hsn_sac_code") or "",
            grand_total=invoice["grand_total"],
        )
        state.gst_exports[export_job.id] = {
            "id": export_job.id,
            "invoice_id": export_job.invoice_id,
            "status": export_job.status,
        }
        invoice["irn_status"] = export_job.status
        append_audit_log(
            action="gst_export.created",
            entity_type="gst_export",
            entity_id=export_job.id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"invoice_id": invoice["id"]},
        )
        return state.gst_exports[export_job.id]

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/compliance/gst-exports/{job_id}/attach-irn")
    def complete_irn_attachment(
        tenant_id: str,
        branch_id: str,
        job_id: str,
        payload: AttachIrnInput,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "compliance.export")
        export_job = state.gst_exports[job_id]
        attachment = attach_irn_to_invoice(
            invoice_id=export_job["invoice_id"],
            irn=payload.irn,
            signed_qr_payload=payload.signed_qr_payload,
            ack_no=payload.ack_no,
        )
        state.irn_attachments[attachment.invoice_id] = asdict(attachment)
        export_job["status"] = "IRN_ATTACHED"
        state.invoices[attachment.invoice_id]["irn_status"] = "IRN_ATTACHED"
        append_audit_log(
            action="irn.attached",
            entity_type="invoice",
            entity_id=attachment.invoice_id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"gst_export_id": job_id},
        )
        return state.irn_attachments[attachment.invoice_id]

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/sales/{sale_id}/returns")
    def create_sale_return(
        tenant_id: str,
        branch_id: str,
        sale_id: str,
        payload: SaleReturnCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "sales.return")
        sale = state.sales[sale_id]
        invoice = state.invoices[sale["invoice_id"]]
        branch = state.branches[branch_id]
        if payload.refund_amount > sale["payment_amount"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refund exceeds paid amount")
        subtotal = 0.0
        stock_after_return = 0.0
        for line in payload.lines:
            sold_line = _find_sale_line(sale, product_id=line.product_id)
            subtotal += _money(sold_line["unit_price"] * line.quantity)
            state.inventory.post_entry(
                item_id=line.product_id,
                branch_id=branch_id,
                quantity=line.quantity,
                entry_type="CUSTOMER_RETURN",
            )
            stock_after_return = state.inventory.stock_on_hand(item_id=line.product_id, branch_id=branch_id)
        tax = calculate_invoice_taxes(
            seller_gstin=branch.get("gstin"),
            buyer_gstin=invoice.get("customer_gstin"),
            taxable_total=_money(subtotal),
            tax_rate_percent=state.products[payload.lines[0].product_id]["tax_rate_percent"],
        )
        credit_note_total = _money(subtotal + tax["tax_total"])
        if payload.refund_amount > credit_note_total:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refund exceeds credit note value")
        sale_return_id = _id()
        credit_note = {
            "id": _id(),
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "sale_return_id": sale_return_id,
            "credit_note_number": next_credit_note_number(state.invoice_sequences, branch_id=branch_id, fiscal_year="2526"),
            "subtotal": _money(subtotal),
            "tax": tax,
            "grand_total": credit_note_total,
        }
        state.credit_notes[credit_note["id"]] = credit_note
        status_value = "REFUND_APPROVED" if can_perform(actor_roles, "refund.approve") else "REFUND_PENDING_APPROVAL"
        sale_return = {
            "id": _id(),
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "sale_id": sale_id,
            "status": status_value,
            "credit_note_id": credit_note["id"],
            "refund_amount": payload.refund_amount,
            "stock_after_return": stock_after_return,
        }
        sale_return["id"] = sale_return_id
        state.sale_returns[sale_return["id"]] = sale_return
        append_audit_log(
            action="credit_note.created",
            entity_type="credit_note",
            entity_id=credit_note["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"credit_note_number": credit_note["credit_note_number"]},
        )
        append_audit_log(
            action="sale_return.created",
            entity_type="sale_return",
            entity_id=sale_return["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"sale_id": sale_id, "refund_amount": payload.refund_amount, "status": status_value},
        )
        if status_value == "REFUND_APPROVED":
            append_audit_log(
                action="sale_return.refund_approved",
                entity_type="sale_return",
                entity_id=sale_return["id"],
                tenant_id=tenant_id,
                branch_id=branch_id,
                actor_roles=actor_roles,
            )
        return {**sale_return, "credit_note": credit_note}

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/sale-returns/{sale_return_id}/approve-refund")
    def approve_sale_return_refund(
        tenant_id: str,
        branch_id: str,
        sale_return_id: str,
        payload: RefundApprovalInput,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "refund.approve")
        sale_return = state.sale_returns[sale_return_id]
        sale_return["status"] = "REFUND_APPROVED"
        append_audit_log(
            action="sale_return.refund_approved",
            entity_type="sale_return",
            entity_id=sale_return_id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"note": payload.note} if payload.note else {},
        )
        return {**sale_return, "credit_note": state.credit_notes[sale_return["credit_note_id"]]}

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/sales/{sale_id}/exchanges")
    def create_exchange_order(
        tenant_id: str,
        branch_id: str,
        sale_id: str,
        payload: ExchangeCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "sales.return")
        sale = state.sales[sale_id]
        return_total = 0.0
        replacement_total = 0.0
        stock_effects = {"returned_products": [], "replacement_products": []}
        for line in payload.return_lines:
            sold_line = _find_sale_line(sale, product_id=line.product_id)
            product = state.products[line.product_id]
            return_total += compute_tax_inclusive_total(
                subtotal=_money(sold_line["unit_price"] * line.quantity),
                tax_rate_percent=product["tax_rate_percent"],
            )
            state.inventory.post_entry(
                item_id=line.product_id,
                branch_id=branch_id,
                quantity=line.quantity,
                entry_type="CUSTOMER_RETURN",
            )
            stock_effects["returned_products"].append(
                {
                    "product_id": line.product_id,
                    "stock_after": state.inventory.stock_on_hand(item_id=line.product_id, branch_id=branch_id),
                }
            )
        for line in payload.replacement_lines:
            product, unit_price = _resolve_branch_pricing(state, branch_id=branch_id, product_id=line.product_id)
            replacement_total += compute_tax_inclusive_total(
                subtotal=_money(unit_price * line.quantity),
                tax_rate_percent=product["tax_rate_percent"],
            )
            state.inventory.post_entry(
                item_id=line.product_id,
                branch_id=branch_id,
                quantity=-line.quantity,
                entry_type="SALE",
            )
            stock_effects["replacement_products"].append(
                {
                    "product_id": line.product_id,
                    "stock_after": state.inventory.stock_on_hand(item_id=line.product_id, branch_id=branch_id),
                }
            )
        exchange_balance = compute_exchange_balance(
            return_total=_money(return_total),
            replacement_total=_money(replacement_total),
        )
        exchange_order = {
            "id": _id(),
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "sale_id": sale_id,
            "return_total": _money(return_total),
            "replacement_total": _money(replacement_total),
            "payment_method": payload.payment_method,
            "cash_session_id": payload.cash_session_id,
            "stock_effects": stock_effects,
            **exchange_balance,
        }
        if payload.cash_session_id:
            cash_session = state.cash_sessions[payload.cash_session_id]
            if cash_session["status"] != "OPEN":
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cash session not open")
            if payload.payment_method == "cash":
                adjustment = exchange_order["balance_amount"]
                if exchange_order["balance_direction"] == "COLLECT_FROM_CUSTOMER":
                    cash_session["cash_sales_total"] = _money(cash_session["cash_sales_total"] + adjustment)
                elif exchange_order["balance_direction"] == "REFUND_TO_CUSTOMER":
                    cash_session["cash_sales_total"] = _money(cash_session["cash_sales_total"] - adjustment)
                cash_session["expected_close_amount"] = _money(cash_session["opening_float"] + cash_session["cash_sales_total"])
        state.exchange_orders[exchange_order["id"]] = exchange_order
        append_audit_log(
            action="exchange.created",
            entity_type="exchange_order",
            entity_id=exchange_order["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"sale_id": sale_id, "balance_direction": exchange_order["balance_direction"]},
        )
        return exchange_order

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-invoices/{purchase_invoice_id}/supplier-returns")
    def create_supplier_return(
        tenant_id: str,
        branch_id: str,
        purchase_invoice_id: str,
        payload: SupplierReturnCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "purchase.manage")
        purchase_invoice = state.purchase_invoices[purchase_invoice_id]
        supplier = state.suppliers[purchase_invoice["supplier_id"]]
        branch = state.branches[branch_id]
        line_inputs: list[dict[str, float]] = []
        return_lines: list[dict[str, Any]] = []
        for line in payload.lines:
            invoice_line = _find_document_line(purchase_invoice["lines"], product_id=line.product_id)
            already_returned_quantity = _returned_supplier_quantity(
                state,
                purchase_invoice_id=purchase_invoice_id,
                product_id=line.product_id,
            )
            available_quantity = _money(invoice_line["quantity"] - already_returned_quantity)
            if line.quantity > available_quantity:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Supplier return exceeds invoiced quantity")
            product = state.products[line.product_id]
            line_inputs.append(
                {
                    "quantity": float(line.quantity),
                    "unit_cost": float(invoice_line["unit_cost"]),
                    "tax_rate_percent": float(product["tax_rate_percent"]),
                }
            )
            state.inventory.post_entry(
                item_id=line.product_id,
                branch_id=branch_id,
                quantity=-line.quantity,
                entry_type="SUPPLIER_RETURN",
            )
            return_lines.append(
                {
                    "product_id": line.product_id,
                    "quantity": line.quantity,
                    "stock_after_return": state.inventory.stock_on_hand(item_id=line.product_id, branch_id=branch_id),
                }
            )
        totals = compute_purchase_totals(
            seller_gstin=supplier.get("gstin"),
            buyer_gstin=branch.get("gstin"),
            lines=line_inputs,
        )
        supplier_return = {
            "id": _id(),
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "purchase_invoice_id": purchase_invoice_id,
            "supplier_id": purchase_invoice["supplier_id"],
            "return_date": date.today().isoformat(),
            "supplier_credit_note_number": next_supplier_credit_note_number(
                state.invoice_sequences,
                branch_id=branch_id,
                fiscal_year="2526",
            ),
            "subtotal": totals["subtotal"],
            "tax": totals["tax"],
            "grand_total": totals["grand_total"],
            "lines": return_lines,
        }
        state.supplier_returns[supplier_return["id"]] = supplier_return
        append_audit_log(
            action="supplier_return.created",
            entity_type="supplier_return",
            entity_id=supplier_return["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"supplier_credit_note_number": supplier_return["supplier_credit_note_number"]},
        )
        return supplier_return

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/purchase-invoices/{purchase_invoice_id}/supplier-payments")
    def create_supplier_payment(
        tenant_id: str,
        branch_id: str,
        purchase_invoice_id: str,
        payload: SupplierPaymentCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "purchase.manage")
        purchase_invoice = state.purchase_invoices.get(purchase_invoice_id)
        if not purchase_invoice or purchase_invoice["tenant_id"] != tenant_id or purchase_invoice["branch_id"] != branch_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase invoice not found")

        credit_note_total = _money(
            sum(
                supplier_return["grand_total"]
                for supplier_return in state.supplier_returns.values()
                if supplier_return["purchase_invoice_id"] == purchase_invoice_id
            )
        )
        paid_total = _money(
            sum(
                supplier_payment["amount"]
                for supplier_payment in state.supplier_payments.values()
                if supplier_payment["purchase_invoice_id"] == purchase_invoice_id
            )
        )
        try:
            ensure_supplier_payment_within_outstanding(
                invoice_total=purchase_invoice["grand_total"],
                credit_note_total=credit_note_total,
                paid_total=paid_total,
                payment_amount=payload.amount,
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        supplier_payment = {
            "id": _id(),
            "tenant_id": tenant_id,
            "branch_id": branch_id,
            "purchase_invoice_id": purchase_invoice_id,
            "supplier_id": purchase_invoice["supplier_id"],
            "payment_number": next_supplier_payment_number(
                state.invoice_sequences,
                branch_id=branch_id,
                fiscal_year="2526",
            ),
            "payment_date": date.today().isoformat(),
            "amount": _money(payload.amount),
            "payment_method": payload.payment_method,
            "reference": payload.reference,
            "outstanding_after_payment": _money(
                purchase_invoice["grand_total"] - credit_note_total - paid_total - _money(payload.amount)
            ),
        }
        state.supplier_payments[supplier_payment["id"]] = supplier_payment
        append_audit_log(
            action="supplier_payment.created",
            entity_type="supplier_payment",
            entity_id=supplier_payment["id"],
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={
                "payment_number": supplier_payment["payment_number"],
                "purchase_invoice_id": purchase_invoice_id,
            },
        )
        return supplier_payment

    @app.post("/v1/tenants/{tenant_id}/branches/{branch_id}/batch-lots/{batch_lot_id}/expiry-write-offs")
    def create_batch_expiry_write_off(
        tenant_id: str,
        branch_id: str,
        batch_lot_id: str,
        payload: ExpiryWriteOffCreate,
        actor_roles: list[str] = Depends(get_actor_roles),
    ) -> dict[str, Any]:
        _require_capability(actor_roles, "inventory.adjust")
        batch_lot = _find_batch_lot(state, tenant_id=tenant_id, branch_id=branch_id, batch_lot_id=batch_lot_id)
        current_report = _build_branch_batch_report(state, tenant_id=tenant_id, branch_id=branch_id)
        current_record = next((record for record in current_report["records"] if record["batch_lot_id"] == batch_lot_id), None)
        if current_record is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No remaining batch quantity available for write-off")
        if payload.quantity > current_record["remaining_quantity"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Expiry write-off exceeds remaining batch quantity")

        batch_lot["written_off_quantity"] = _money(batch_lot.get("written_off_quantity", 0.0) + payload.quantity)
        state.inventory.post_entry(
            item_id=batch_lot["product_id"],
            branch_id=branch_id,
            quantity=-payload.quantity,
            entry_type="EXPIRY_WRITE_OFF",
        )
        updated_report = _build_branch_batch_report(state, tenant_id=tenant_id, branch_id=branch_id)
        updated_record = next((record for record in updated_report["records"] if record["batch_lot_id"] == batch_lot_id), None)
        append_audit_log(
            action="batch_lot.expiry_written_off",
            entity_type="batch_lot",
            entity_id=batch_lot_id,
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_roles=actor_roles,
            details={"quantity": _money(payload.quantity), "reason": payload.reason},
        )
        return {
            **batch_lot,
            "written_off_quantity": _money(batch_lot["written_off_quantity"]),
            "remaining_quantity": updated_record["remaining_quantity"] if updated_record else 0.0,
        }

    @app.post("/v1/sync/push")
    def push_sync_record(payload: SyncPushInput, actor_roles: list[str] = Depends(get_actor_roles)) -> dict[str, Any]:
        _require_capability(actor_roles, "sales.bill")
        result = resolve_mutation_conflict(
            client_version=payload.client_version,
            server_version=payload.server_version,
        )
        state.sync_records.append(
            {
                "id": payload.record_id,
                "version": result.next_version if result.accepted else payload.server_version,
            }
        )
        return {
            "accepted": result.accepted,
            "conflict": result.conflict,
            "next_version": result.next_version,
        }

    @app.get("/v1/sync/pull")
    def pull_sync_records() -> dict[str, Any]:
        return build_pull_response(state.sync_records)

    @app.get("/v1/sync/heartbeat")
    def sync_heartbeat() -> dict[str, str]:
        return {"status": "current"}

    return app
