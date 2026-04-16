from __future__ import annotations

from collections import defaultdict

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AuditRepository, BatchRepository, CatalogRepository, InventoryRepository, TenantRepository
from ..utils import utc_now
from .batches_policy import (
    batch_expiry_session_number,
    build_batch_expiry_board,
    build_batch_expiry_report,
    ensure_batch_expiry_review_approvable,
    ensure_batch_expiry_review_cancelable,
    ensure_batch_expiry_review_recordable,
    ensure_expiry_write_off_allowed,
    validate_goods_receipt_batch_lots,
)


class BatchService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._catalog_repo = CatalogRepository(session)
        self._inventory_repo = InventoryRepository(session)
        self._batch_repo = BatchRepository(session)
        self._audit_repo = AuditRepository(session)

    async def create_goods_receipt_batch_lots(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        goods_receipt_id: str,
        actor_user_id: str,
        lots: list[dict[str, object]],
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

        goods_receipt = await self._inventory_repo.get_goods_receipt(
            tenant_id=tenant_id,
            branch_id=branch_id,
            goods_receipt_id=goods_receipt_id,
        )
        if goods_receipt is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goods receipt not found")

        existing_batch_lots = await self._batch_repo.list_batch_lots_for_goods_receipt(goods_receipt_id=goods_receipt_id)
        if existing_batch_lots:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Batch lots already recorded for goods receipt")

        receipt_lines = (
            await self._inventory_repo.list_goods_receipt_lines_for_receipts(goods_receipt_ids=[goods_receipt_id])
        ).get(goods_receipt_id, [])
        normalized_lots = [
            {
                "product_id": str(lot["product_id"]),
                "batch_number": str(lot["batch_number"]),
                "quantity": float(lot["quantity"]),
                "expiry_date": lot["expiry_date"],
            }
            for lot in lots
        ]
        try:
            validate_goods_receipt_batch_lots(
                goods_receipt_lines=[
                    {
                        "product_id": line.product_id,
                        "quantity": line.quantity,
                    }
                    for line in receipt_lines
                ],
                lots=normalized_lots,
            )
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        records = await self._batch_repo.create_batch_lots(
            tenant_id=tenant_id,
            branch_id=branch_id,
            goods_receipt_id=goods_receipt_id,
            lots=normalized_lots,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="batch_lots.recorded",
            entity_type="goods_receipt",
            entity_id=goods_receipt_id,
            payload={"batch_lot_count": len(records)},
        )
        await self._session.commit()
        return {
            "goods_receipt_id": goods_receipt_id,
            "records": [
                {
                    "id": record.id,
                    "product_id": record.product_id,
                    "batch_number": record.batch_number,
                    "quantity": round(record.quantity, 2),
                    "expiry_date": record.expiry_date,
                }
                for record in records
            ],
        }

    async def batch_expiry_report(self, *, tenant_id: str, branch_id: str) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

        batch_lots = await self._batch_repo.list_branch_batch_lots(tenant_id=tenant_id, branch_id=branch_id)
        write_off_records = await self._batch_repo.list_write_offs_for_batch_lots(batch_lot_ids=[record.id for record in batch_lots])
        write_offs_by_batch_lot_id: dict[str, float] = defaultdict(float)
        for batch_lot_id, records in write_off_records.items():
            write_offs_by_batch_lot_id[batch_lot_id] = round(sum(record.quantity for record in records), 2)

        products_by_id = {
            product.id: {"name": product.name, "sku_code": product.sku_code}
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }
        ledger_entries = await self._inventory_repo.list_branch_inventory_ledger(tenant_id=tenant_id, branch_id=branch_id)
        stock_by_product: dict[str, float] = defaultdict(float)
        for entry in ledger_entries:
            stock_by_product[entry.product_id] = round(stock_by_product[entry.product_id] + float(entry.quantity), 2)

        report = build_batch_expiry_report(
            batch_lots=[
                {
                    "id": record.id,
                    "product_id": record.product_id,
                    "batch_number": record.batch_number,
                    "quantity": record.quantity,
                    "expiry_date": record.expiry_date,
                }
                for record in batch_lots
            ],
            write_offs_by_batch_lot_id=dict(write_offs_by_batch_lot_id),
            products_by_id=products_by_id,
            stock_by_product=dict(stock_by_product),
            as_of=utc_now().date(),
        )
        return {"branch_id": branch_id, **report}

    async def batch_expiry_board(self, *, tenant_id: str, branch_id: str) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

        review_sessions = await self._batch_repo.list_branch_batch_expiry_review_sessions(tenant_id=tenant_id, branch_id=branch_id)
        products_by_id = {
            product.id: {"product_name": product.name, "sku_code": product.sku_code}
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }
        batch_lots = {
            lot.id: lot
            for lot in await self._batch_repo.list_branch_batch_lots(tenant_id=tenant_id, branch_id=branch_id)
        }
        return build_batch_expiry_board(
            branch_id=branch_id,
            review_sessions=[
                {
                    "batch_expiry_session_id": session.id,
                    "session_number": session.session_number,
                    "batch_lot_id": session.batch_lot_id,
                    "product_id": session.product_id,
                    "batch_number": batch_lots.get(session.batch_lot_id).batch_number if batch_lots.get(session.batch_lot_id) is not None else session.batch_lot_id,
                    "status": session.status,
                    "remaining_quantity_snapshot": session.remaining_quantity_snapshot,
                    "proposed_quantity": session.proposed_quantity,
                    "reason": session.reason,
                    "note": session.note,
                    "review_note": session.review_note,
                }
                for session in review_sessions
            ],
            products_by_id=products_by_id,
        )

    async def create_batch_expiry_review_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        batch_lot_id: str,
        actor_user_id: str,
        note: str | None,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

        batch_lot = await self._batch_repo.get_batch_lot(tenant_id=tenant_id, branch_id=branch_id, batch_lot_id=batch_lot_id)
        if batch_lot is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch lot not found")

        current_report = await self.batch_expiry_report(tenant_id=tenant_id, branch_id=branch_id)
        current_record = next((record for record in current_report["records"] if record["batch_lot_id"] == batch_lot_id), None)
        remaining_quantity = 0.0 if current_record is None else float(current_record["remaining_quantity"])
        if remaining_quantity <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No remaining batch quantity available for write-off")

        existing_sessions = await self._batch_repo.list_branch_batch_expiry_review_sessions(tenant_id=tenant_id, branch_id=branch_id)
        if any(session.batch_lot_id == batch_lot_id and session.status in {"OPEN", "REVIEWED"} for session in existing_sessions):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Batch lot already has an active expiry review session")

        sequence_number = await self._batch_repo.next_branch_batch_expiry_review_sequence(tenant_id=tenant_id, branch_id=branch_id)
        record = await self._batch_repo.create_batch_expiry_review_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            batch_lot_id=batch_lot_id,
            product_id=batch_lot.product_id,
            session_number=batch_expiry_session_number(branch_code=branch.code, sequence_number=sequence_number),
            remaining_quantity_snapshot=remaining_quantity,
            note=note.strip() if note is not None and note.strip() else None,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="batch_expiry_session.created",
            entity_type="batch_lot",
            entity_id=batch_lot_id,
            payload={"batch_expiry_session_id": record.id},
        )
        await self._session.commit()
        return self._serialize_batch_expiry_review_session(record)

    async def record_batch_expiry_review_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        batch_expiry_session_id: str,
        actor_user_id: str,
        quantity: float,
        reason: str,
    ) -> dict[str, object]:
        session_record = await self._batch_repo.get_batch_expiry_review_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            batch_expiry_session_id=batch_expiry_session_id,
        )
        if session_record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch expiry review session not found")

        try:
            ensure_batch_expiry_review_recordable(status=session_record.status)
            ensure_expiry_write_off_allowed(remaining_quantity=session_record.remaining_quantity_snapshot, quantity=quantity)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        session_record.proposed_quantity = round(float(quantity), 2)
        session_record.reason = reason.strip()
        session_record.status = "REVIEWED"
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="batch_expiry_session.reviewed",
            entity_type="batch_expiry_session",
            entity_id=batch_expiry_session_id,
            payload={"quantity": session_record.proposed_quantity, "reason": session_record.reason},
        )
        await self._session.commit()
        return self._serialize_batch_expiry_review_session(session_record)

    async def approve_batch_expiry_review_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        batch_expiry_session_id: str,
        actor_user_id: str,
        review_note: str | None,
    ) -> dict[str, object]:
        session_record = await self._batch_repo.get_batch_expiry_review_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            batch_expiry_session_id=batch_expiry_session_id,
        )
        if session_record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch expiry review session not found")

        try:
            ensure_batch_expiry_review_approvable(status=session_record.status)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        current_report = await self.batch_expiry_report(tenant_id=tenant_id, branch_id=branch_id)
        current_record = next((record for record in current_report["records"] if record["batch_lot_id"] == session_record.batch_lot_id), None)
        remaining_quantity = 0.0 if current_record is None else float(current_record["remaining_quantity"])
        try:
            ensure_expiry_write_off_allowed(remaining_quantity=remaining_quantity, quantity=float(session_record.proposed_quantity or 0.0))
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        batch_lot = await self._batch_repo.get_batch_lot(tenant_id=tenant_id, branch_id=branch_id, batch_lot_id=session_record.batch_lot_id)
        if batch_lot is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch lot not found")

        write_off = await self._batch_repo.create_batch_expiry_write_off(
            tenant_id=tenant_id,
            branch_id=branch_id,
            batch_lot_id=session_record.batch_lot_id,
            product_id=session_record.product_id,
            quantity=float(session_record.proposed_quantity or 0.0),
            reason=str(session_record.reason or ""),
        )
        await self._inventory_repo.create_inventory_ledger_entries(
            entries=[
                {
                    "tenant_id": tenant_id,
                    "branch_id": branch_id,
                    "product_id": session_record.product_id,
                    "entry_type": "EXPIRY_WRITE_OFF",
                    "quantity": -abs(float(session_record.proposed_quantity or 0.0)),
                    "reference_type": "batch_expiry_write_off",
                    "reference_id": write_off.id,
                }
            ]
        )

        session_record.status = "APPROVED"
        session_record.review_note = review_note.strip() if review_note is not None and review_note.strip() else None
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="batch_expiry_session.approved",
            entity_type="batch_expiry_session",
            entity_id=batch_expiry_session_id,
            payload={"write_off_id": write_off.id},
        )
        await self._session.commit()

        updated_report = await self.batch_expiry_report(tenant_id=tenant_id, branch_id=branch_id)
        updated_record = next((record for record in updated_report["records"] if record["batch_lot_id"] == session_record.batch_lot_id), None)
        products = await self._catalog_repo.list_products(tenant_id=tenant_id)
        product = next((item for item in products if item.id == session_record.product_id), None)
        return {
            "session": self._serialize_batch_expiry_review_session(session_record),
            "write_off": {
                "batch_lot_id": session_record.batch_lot_id,
                "product_id": session_record.product_id,
                "product_name": product.name if product is not None else session_record.product_id,
                "batch_number": batch_lot.batch_number,
                "expiry_date": batch_lot.expiry_date,
                "received_quantity": round(batch_lot.quantity, 2),
                "written_off_quantity": round(sum(record.quantity for record in (await self._batch_repo.list_write_offs_for_batch_lots(batch_lot_ids=[session_record.batch_lot_id])).get(session_record.batch_lot_id, [])), 2),
                "remaining_quantity": 0.0 if updated_record is None else updated_record["remaining_quantity"],
                "status": "WRITTEN_OFF" if updated_record is None else updated_record["status"],
                "reason": session_record.reason,
            },
        }

    async def cancel_batch_expiry_review_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        batch_expiry_session_id: str,
        actor_user_id: str,
        review_note: str | None,
    ) -> dict[str, object]:
        session_record = await self._batch_repo.get_batch_expiry_review_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            batch_expiry_session_id=batch_expiry_session_id,
        )
        if session_record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch expiry review session not found")

        try:
            ensure_batch_expiry_review_cancelable(status=session_record.status)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        session_record.status = "CANCELED"
        session_record.review_note = review_note.strip() if review_note is not None and review_note.strip() else None
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="batch_expiry_session.canceled",
            entity_type="batch_expiry_session",
            entity_id=batch_expiry_session_id,
            payload={"review_note": session_record.review_note},
        )
        await self._session.commit()
        return self._serialize_batch_expiry_review_session(session_record)

    async def create_batch_expiry_write_off(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        batch_lot_id: str,
        actor_user_id: str,
        quantity: float,
        reason: str,
    ) -> dict[str, object]:
        batch_lot = await self._batch_repo.get_batch_lot(tenant_id=tenant_id, branch_id=branch_id, batch_lot_id=batch_lot_id)
        if batch_lot is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch lot not found")

        current_report = await self.batch_expiry_report(tenant_id=tenant_id, branch_id=branch_id)
        current_record = next((record for record in current_report["records"] if record["batch_lot_id"] == batch_lot_id), None)
        remaining_quantity = 0.0 if current_record is None else float(current_record["remaining_quantity"])
        try:
            ensure_expiry_write_off_allowed(remaining_quantity=remaining_quantity, quantity=quantity)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        write_off = await self._batch_repo.create_batch_expiry_write_off(
            tenant_id=tenant_id,
            branch_id=branch_id,
            batch_lot_id=batch_lot_id,
            product_id=batch_lot.product_id,
            quantity=quantity,
            reason=reason,
        )
        await self._inventory_repo.create_inventory_ledger_entries(
            entries=[
                {
                    "tenant_id": tenant_id,
                    "branch_id": branch_id,
                    "product_id": batch_lot.product_id,
                    "entry_type": "EXPIRY_WRITE_OFF",
                    "quantity": -abs(quantity),
                    "reference_type": "batch_expiry_write_off",
                    "reference_id": write_off.id,
                }
            ]
        )
        updated_report = await self.batch_expiry_report(tenant_id=tenant_id, branch_id=branch_id)
        updated_record = next((record for record in updated_report["records"] if record["batch_lot_id"] == batch_lot_id), None)
        write_off_records = await self._batch_repo.list_write_offs_for_batch_lots(batch_lot_ids=[batch_lot_id])
        written_off_quantity = round(sum(record.quantity for record in write_off_records.get(batch_lot_id, [])), 2)
        products = await self._catalog_repo.list_products(tenant_id=tenant_id)
        product = next((item for item in products if item.id == batch_lot.product_id), None)
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="batch_lot.expiry_written_off",
            entity_type="batch_lot",
            entity_id=batch_lot_id,
            payload={"quantity": round(float(quantity), 2), "reason": reason},
        )
        await self._session.commit()
        return {
            "batch_lot_id": batch_lot_id,
            "product_id": batch_lot.product_id,
            "product_name": product.name if product is not None else batch_lot.product_id,
            "batch_number": batch_lot.batch_number,
            "expiry_date": batch_lot.expiry_date,
            "received_quantity": round(batch_lot.quantity, 2),
            "written_off_quantity": written_off_quantity,
            "remaining_quantity": 0.0 if updated_record is None else updated_record["remaining_quantity"],
            "status": "WRITTEN_OFF" if updated_record is None else updated_record["status"],
            "reason": reason,
        }

    @staticmethod
    def _serialize_batch_expiry_review_session(session_record: object) -> dict[str, object]:
        return {
            "id": session_record.id,
            "tenant_id": session_record.tenant_id,
            "branch_id": session_record.branch_id,
            "batch_lot_id": session_record.batch_lot_id,
            "product_id": session_record.product_id,
            "session_number": session_record.session_number,
            "status": session_record.status,
            "remaining_quantity_snapshot": round(float(session_record.remaining_quantity_snapshot), 2),
            "proposed_quantity": None if session_record.proposed_quantity is None else round(float(session_record.proposed_quantity), 2),
            "reason": session_record.reason,
            "note": session_record.note,
            "review_note": session_record.review_note,
        }
