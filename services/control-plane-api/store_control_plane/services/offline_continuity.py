from __future__ import annotations

import json
from datetime import datetime
from hashlib import sha256

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AuditRepository, BillingRepository, CatalogRepository, InventoryRepository, SyncRuntimeRepository, TenantRepository
from ..utils import utc_now
from .billing_policy import SaleDraft, build_sale_draft, sale_invoice_number
from .commercial_access import CommercialAccessService
from .sync_runtime_auth import SyncDeviceContext


def _money(value: float | int) -> float:
    return round(float(value) + 1e-9, 2)


def _request_hash(payload: dict[str, object]) -> str:
    return sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def _parse_issued_on(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


class OfflineContinuityService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._catalog_repo = CatalogRepository(session)
        self._inventory_repo = InventoryRepository(session)
        self._billing_repo = BillingRepository(session)
        self._sync_repo = SyncRuntimeRepository(session)
        self._audit_repo = AuditRepository(session)
        self._commercial_access = CommercialAccessService(session)

    async def replay_offline_sale(
        self,
        *,
        device: SyncDeviceContext,
        payload: dict[str, object],
    ) -> dict[str, object]:
        await self._commercial_access.assert_offline_continuity_allowed(tenant_id=device.tenant_id)
        branch = await self._tenant_repo.get_branch(tenant_id=device.tenant_id, branch_id=device.branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

        existing_envelope = await self._sync_repo.get_sync_envelope(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            device_id=device.device_id,
            idempotency_key=str(payload["idempotency_key"]),
            direction="INGRESS",
        )
        if existing_envelope is not None:
            duplicate_response = dict(existing_envelope.response_payload)
            duplicate_response["duplicate"] = True
            return duplicate_response

        envelope = await self._sync_repo.create_sync_envelope(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            device_id=device.device_id,
            idempotency_key=str(payload["idempotency_key"]),
            direction="INGRESS",
            entity_type="offline_sale_replay",
            entity_id=str(payload["continuity_sale_id"]),
            payload_json=_json_ready(payload),
        )

        if branch.gstin is None:
            return await self._record_conflict(
                device=device,
                envelope=envelope,
                payload=payload,
                reason="BRANCH_GSTIN_MISSING",
                message="Branch GSTIN is required before offline sales can be replayed",
            )

        products = {product.id: product for product in await self._catalog_repo.list_products(tenant_id=device.tenant_id)}
        branch_catalog_items = await self._catalog_repo.list_branch_catalog_items(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
        )
        branch_catalog_by_product_id: dict[str, dict[str, object]] = {}
        for item in branch_catalog_items:
            product = products.get(item.product_id)
            if product is None:
                continue
            branch_catalog_by_product_id[item.product_id] = {
                "availability_status": item.availability_status,
                "effective_selling_price": item.selling_price_override if item.selling_price_override is not None else product.selling_price,
            }

        try:
            draft = build_sale_draft(
                line_inputs=[
                    {
                        "product_id": line["product_id"],
                        "quantity": line["quantity"],
                    }
                    for line in list(payload["lines"])
                ],
                branch_gstin=branch.gstin,
                customer_name=str(payload["customer_name"]),
                customer_gstin=str(payload["customer_gstin"]) if payload.get("customer_gstin") else None,
                products_by_id=products,
                branch_catalog_items_by_product_id=branch_catalog_by_product_id,
            )
        except ValueError as error:
            return await self._record_conflict(
                device=device,
                envelope=envelope,
                payload=payload,
                reason="DRAFT_MISMATCH",
                message=str(error),
            )

        draft_mismatch = self._detect_draft_mismatch(payload=payload, draft=draft)
        if draft_mismatch is not None:
            return await self._record_conflict(
                device=device,
                envelope=envelope,
                payload=payload,
                reason="DRAFT_MISMATCH",
                message=draft_mismatch,
            )

        stock_divergence = await self._detect_stock_divergence(device=device, payload=payload)
        if stock_divergence is not None:
            return await self._record_conflict(
                device=device,
                envelope=envelope,
                payload=payload,
                reason="STOCK_DIVERGENCE",
                message=stock_divergence,
            )

        sequence_number = await self._billing_repo.next_branch_sale_sequence(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
        )
        invoice_number = sale_invoice_number(branch_code=branch.code, sequence_number=sequence_number)
        persisted = await self._billing_repo.create_sale(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            customer_profile_id=None,
            customer_name=draft.customer_name,
            customer_gstin=draft.customer_gstin,
            invoice_kind=draft.invoice_kind,
            irn_status=draft.irn_status,
            issued_on=_parse_issued_on(payload["issued_offline_at"]).date(),
            invoice_number=invoice_number,
            subtotal=draft.subtotal,
            tax_total=draft.tax_total,
            cgst_total=draft.cgst_total,
            sgst_total=draft.sgst_total,
            igst_total=draft.igst_total,
            grand_total=draft.grand_total,
            loyalty_points_redeemed=0,
            loyalty_discount_amount=0.0,
            loyalty_points_earned=0,
            payment_method=str(payload["payment_method"]),
            payments=None,
            lines=[
                {
                    "product_id": line.product_id,
                    "quantity": line.quantity,
                    "unit_price": line.unit_price,
                    "gst_rate": line.gst_rate,
                    "line_subtotal": line.line_subtotal,
                    "tax_total": line.tax_total,
                    "line_total": line.line_total,
                }
                for line in draft.lines
            ],
            tax_lines=[
                {
                    "tax_type": line.tax_type,
                    "tax_rate": line.tax_rate,
                    "taxable_amount": line.taxable_amount,
                    "tax_amount": line.tax_amount,
                }
                for line in draft.tax_lines
            ],
        )
        await self._inventory_repo.create_inventory_ledger_entries(
            entries=[
                {
                    "tenant_id": device.tenant_id,
                    "branch_id": device.branch_id,
                    "product_id": line.product_id,
                    "entry_type": "SALE",
                    "quantity": -abs(line.quantity),
                    "reference_type": "sale",
                    "reference_id": persisted.sale.id,
                }
                for line in draft.lines
            ]
        )

        current_cursor = await self._sync_repo.get_latest_branch_cursor(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
        )
        await self._sync_repo.create_sync_mutation(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            device_id=device.device_id,
            idempotency_key=str(payload["idempotency_key"]),
            table_name="sales",
            record_id=persisted.sale.id,
            operation="UPSERT",
            client_version=1,
            expected_server_version=current_cursor,
            server_version=current_cursor + 1,
            request_hash=_request_hash(
                {
                    "continuity_sale_id": payload["continuity_sale_id"],
                    "sale_id": persisted.sale.id,
                    "invoice_number": invoice_number,
                }
            ),
            payload_json={
                "sale_id": persisted.sale.id,
                "invoice_number": invoice_number,
                "continuity_sale_id": str(payload["continuity_sale_id"]),
                "continuity_invoice_number": str(payload["continuity_invoice_number"]),
            },
        )
        branch_cursor = await self._sync_repo.get_latest_branch_cursor(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
        )
        await self._sync_repo.upsert_hub_sync_status(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            hub_device_id=device.device_id,
            source_device_id=device.device_code,
            updates={
                "last_successful_push_at": utc_now(),
                "last_successful_push_mutations": 1,
                "last_idempotency_key": str(payload["idempotency_key"]),
                "branch_cursor": branch_cursor,
            },
        )
        response = {
            "result": "accepted",
            "duplicate": False,
            "continuity_sale_id": str(payload["continuity_sale_id"]),
            "sale_id": persisted.sale.id,
            "invoice_number": invoice_number,
            "conflict_id": None,
            "message": None,
        }
        await self._sync_repo.finalize_sync_envelope(
            envelope=envelope,
            status="SYNCED",
            response_payload=_json_ready(response),
        )
        await self._audit_repo.record(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            actor_user_id=str(payload["staff_actor_id"]),
            action="offline_sale.replayed",
            entity_type="sale",
            entity_id=persisted.sale.id,
            payload={
                "invoice_number": invoice_number,
                "continuity_sale_id": str(payload["continuity_sale_id"]),
                "continuity_invoice_number": str(payload["continuity_invoice_number"]),
            },
        )
        await self._session.commit()
        return response

    async def _record_conflict(
        self,
        *,
        device: SyncDeviceContext,
        envelope,
        payload: dict[str, object],
        reason: str,
        message: str,
    ) -> dict[str, object]:
        branch_cursor = await self._sync_repo.get_latest_branch_cursor(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
        )
        conflict = await self._sync_repo.create_sync_conflict(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            device_id=device.device_id,
            source_idempotency_key=str(payload["idempotency_key"]),
            conflict_index=0,
            request_hash=_request_hash(payload),
            table_name="offline_sales",
            record_id=str(payload["continuity_sale_id"]),
            reason=reason,
            message=message,
            client_version=1,
            server_version=branch_cursor,
            retry_strategy="MANUAL_REVIEW",
        )
        await self._sync_repo.upsert_hub_sync_status(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            hub_device_id=device.device_id,
            source_device_id=device.device_code,
            updates={
                "last_idempotency_key": str(payload["idempotency_key"]),
                "branch_cursor": branch_cursor,
            },
        )
        response = {
            "result": "conflict_review_required",
            "duplicate": False,
            "continuity_sale_id": str(payload["continuity_sale_id"]),
            "sale_id": None,
            "invoice_number": None,
            "conflict_id": conflict.id,
            "message": message,
        }
        await self._sync_repo.finalize_sync_envelope(
            envelope=envelope,
            status="CONFLICT",
            response_payload=_json_ready(response),
            last_error=message,
        )
        await self._audit_repo.record(
            tenant_id=device.tenant_id,
            branch_id=device.branch_id,
            actor_user_id=str(payload["staff_actor_id"]),
            action="offline_sale.replay_conflict",
            entity_type="offline_sale",
            entity_id=str(payload["continuity_sale_id"]),
            payload={
                "reason": reason,
                "message": message,
                "idempotency_key": str(payload["idempotency_key"]),
            },
        )
        await self._session.commit()
        return response

    async def _detect_stock_divergence(
        self,
        *,
        device: SyncDeviceContext,
        payload: dict[str, object],
    ) -> str | None:
        for line in list(payload["lines"]):
            available_quantity = await self._inventory_repo.stock_on_hand(
                tenant_id=device.tenant_id,
                branch_id=device.branch_id,
                product_id=str(line["product_id"]),
            )
            requested_quantity = _money(line["quantity"])
            if requested_quantity > _money(available_quantity):
                return (
                    f"Offline sale requested {requested_quantity} units for product {line['product_id']}, "
                    f"but only {available_quantity} remain in cloud stock"
                )
        return None

    def _detect_draft_mismatch(
        self,
        *,
        payload: dict[str, object],
        draft: SaleDraft,
    ) -> str | None:
        expected_totals = {
            "subtotal": draft.subtotal,
            "cgst_total": draft.cgst_total,
            "sgst_total": draft.sgst_total,
            "igst_total": draft.igst_total,
            "grand_total": draft.grand_total,
        }
        for field_name, expected_value in expected_totals.items():
            payload_value = _money(payload[field_name])
            if payload_value != _money(expected_value):
                return f"Offline sale {field_name} no longer matches the authoritative billing draft"
        if str(payload["customer_name"]).strip() != draft.customer_name:
            return "Offline sale customer name no longer matches the authoritative billing draft"
        if payload.get("customer_gstin") != draft.customer_gstin:
            return "Offline sale customer GSTIN no longer matches the authoritative billing draft"
        return None
