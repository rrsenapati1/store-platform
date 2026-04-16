from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import AuditRepository, CatalogRepository, InventoryRepository, PurchasingRepository, TenantRepository
from ..utils import utc_now
from .inventory_policy import (
    SUPPORTED_LEDGER_ENTRY_TYPES,
    SUPPORTED_RESTOCK_SOURCE_POSTURES,
    build_stock_count_board,
    build_goods_receipt_lines,
    build_inventory_snapshot,
    build_replenishment_board,
    build_restock_board,
    build_receiving_board,
    build_stock_count_result,
    build_transfer_board,
    ensure_restock_task_cancelable,
    ensure_restock_task_completable,
    ensure_restock_task_creatable,
    ensure_restock_task_pickable,
    ensure_stock_count_review_approvable,
    ensure_stock_count_review_cancelable,
    ensure_stock_count_review_recordable,
    ensure_purchase_order_receivable,
    ensure_stock_adjustment_allowed,
    ensure_transfer_allowed,
    goods_receipt_number,
    restock_task_number,
    stock_count_session_number,
    transfer_number,
)


class InventoryService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._catalog_repo = CatalogRepository(session)
        self._inventory_repo = InventoryRepository(session)
        self._purchasing_repo = PurchasingRepository(session)
        self._audit_repo = AuditRepository(session)

    async def create_goods_receipt(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        purchase_order_id: str,
        note: str | None = None,
        lines: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

        purchase_order = await self._purchasing_repo.get_purchase_order(
            tenant_id=tenant_id,
            branch_id=branch_id,
            purchase_order_id=purchase_order_id,
        )
        if purchase_order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")

        existing_goods_receipt = await self._inventory_repo.get_goods_receipt_for_purchase_order(
            tenant_id=tenant_id,
            branch_id=branch_id,
            purchase_order_id=purchase_order_id,
        )
        try:
            ensure_purchase_order_receivable(
                purchase_order=purchase_order,
                existing_goods_receipt={"goods_receipt_id": existing_goods_receipt.id} if existing_goods_receipt is not None else None,
            )
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        purchase_order_lines = (
            await self._purchasing_repo.list_purchase_order_lines_for_orders(purchase_order_ids=[purchase_order.id])
        ).get(purchase_order.id, [])
        if not purchase_order_lines:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Purchase order has no lines to receive")

        products_by_id = {
            product.id: product
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }
        line_drafts = build_goods_receipt_lines(
            purchase_order_lines=purchase_order_lines,
            reviewed_lines=lines,
            products_by_id=products_by_id,
        )
        sequence_number = await self._inventory_repo.next_branch_goods_receipt_sequence(
            tenant_id=tenant_id,
            branch_id=branch_id,
        )
        goods_receipt = await self._inventory_repo.create_goods_receipt(
            tenant_id=tenant_id,
            branch_id=branch_id,
            purchase_order_id=purchase_order.id,
            supplier_id=purchase_order.supplier_id,
            goods_receipt_number=goods_receipt_number(branch_code=branch.code, sequence_number=sequence_number),
            received_on=utc_now().date(),
            note=note,
            lines=[
                {
                    "product_id": line.product_id,
                    "ordered_quantity": line.ordered_quantity,
                    "quantity": line.quantity,
                    "unit_cost": line.unit_cost,
                    "line_total": line.line_total,
                    "discrepancy_note": line.discrepancy_note,
                }
                for line in line_drafts
            ],
        )
        await self._inventory_repo.create_inventory_ledger_entries(
            entries=[
                {
                    "tenant_id": tenant_id,
                    "branch_id": branch_id,
                    "product_id": line.product_id,
                    "entry_type": "PURCHASE_RECEIPT",
                    "quantity": line.quantity,
                    "reference_type": "goods_receipt",
                    "reference_id": goods_receipt.id,
                }
                for line in line_drafts
                if line.quantity > 0
            ]
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="goods_receipt.created",
            entity_type="goods_receipt",
            entity_id=goods_receipt.id,
            payload={
                "goods_receipt_number": goods_receipt.goods_receipt_number,
                "purchase_order_id": purchase_order.id,
                "has_discrepancy": any(line.variance_quantity != 0 for line in line_drafts),
            },
        )
        await self._session.commit()
        ordered_quantity_total = round(sum(line.ordered_quantity for line in line_drafts), 2)
        received_quantity_total = round(sum(line.quantity for line in line_drafts), 2)
        variance_quantity_total = round(sum(line.variance_quantity for line in line_drafts), 2)
        return {
            "id": goods_receipt.id,
            "tenant_id": goods_receipt.tenant_id,
            "branch_id": goods_receipt.branch_id,
            "purchase_order_id": goods_receipt.purchase_order_id,
            "supplier_id": goods_receipt.supplier_id,
            "goods_receipt_number": goods_receipt.goods_receipt_number,
            "received_on": goods_receipt.received_on,
            "note": goods_receipt.note,
            "ordered_quantity_total": ordered_quantity_total,
            "received_quantity_total": received_quantity_total,
            "variance_quantity_total": variance_quantity_total,
            "has_discrepancy": variance_quantity_total != 0,
            "lines": [
                {
                    "product_id": line.product_id,
                    "product_name": line.product_name,
                    "sku_code": line.sku_code,
                    "ordered_quantity": line.ordered_quantity,
                    "quantity": line.quantity,
                    "variance_quantity": line.variance_quantity,
                    "unit_cost": line.unit_cost,
                    "line_total": line.line_total,
                    "discrepancy_note": line.discrepancy_note,
                }
                for line in line_drafts
            ],
        }

    async def list_goods_receipts(self, *, tenant_id: str, branch_id: str) -> list[dict[str, object]]:
        await self._assert_branch_exists(tenant_id=tenant_id, branch_id=branch_id)
        goods_receipts = await self._inventory_repo.list_branch_goods_receipts(tenant_id=tenant_id, branch_id=branch_id)
        lines_by_receipt_id = await self._inventory_repo.list_goods_receipt_lines_for_receipts(
            goods_receipt_ids=[goods_receipt.id for goods_receipt in goods_receipts]
        )
        purchase_orders = {
            purchase_order.id: purchase_order
            for purchase_order in await self._purchasing_repo.list_branch_purchase_orders(tenant_id=tenant_id, branch_id=branch_id)
        }
        suppliers = {
            supplier.id: supplier
            for supplier in await self._purchasing_repo.list_suppliers(tenant_id=tenant_id)
        }
        return [
            {
                "goods_receipt_id": goods_receipt.id,
                "goods_receipt_number": goods_receipt.goods_receipt_number,
                "purchase_order_id": goods_receipt.purchase_order_id,
                "purchase_order_number": purchase_orders[goods_receipt.purchase_order_id].purchase_order_number
                if goods_receipt.purchase_order_id in purchase_orders
                else goods_receipt.purchase_order_id,
                "supplier_id": goods_receipt.supplier_id,
                "supplier_name": suppliers[goods_receipt.supplier_id].name
                if goods_receipt.supplier_id in suppliers
                else goods_receipt.supplier_id,
                "received_on": goods_receipt.received_on,
                "line_count": len(lines_by_receipt_id.get(goods_receipt.id, [])),
                "received_quantity": round(
                    sum(line.quantity for line in lines_by_receipt_id.get(goods_receipt.id, [])),
                    2,
                ),
                "ordered_quantity": round(
                    sum(line.ordered_quantity for line in lines_by_receipt_id.get(goods_receipt.id, [])),
                    2,
                ),
                "variance_quantity": round(
                    sum(max(line.ordered_quantity - line.quantity, 0.0) for line in lines_by_receipt_id.get(goods_receipt.id, [])),
                    2,
                ),
                "has_discrepancy": any(line.ordered_quantity != line.quantity for line in lines_by_receipt_id.get(goods_receipt.id, [])),
                "note": goods_receipt.note,
            }
            for goods_receipt in goods_receipts
        ]

    async def receiving_board(self, *, tenant_id: str, branch_id: str) -> dict[str, object]:
        await self._assert_branch_exists(tenant_id=tenant_id, branch_id=branch_id)
        purchase_orders = await self._build_purchase_order_records(tenant_id=tenant_id, branch_id=branch_id)
        goods_receipts = await self.list_goods_receipts(tenant_id=tenant_id, branch_id=branch_id)
        suppliers = {
            supplier.id: {"name": supplier.name}
            for supplier in await self._purchasing_repo.list_suppliers(tenant_id=tenant_id)
        }
        return build_receiving_board(
            branch_id=branch_id,
            purchase_orders=purchase_orders,
            suppliers_by_id=suppliers,
            goods_receipts=goods_receipts,
        )

    async def inventory_ledger(self, *, tenant_id: str, branch_id: str) -> list[dict[str, object]]:
        await self._assert_branch_exists(tenant_id=tenant_id, branch_id=branch_id)
        entries = await self._inventory_repo.list_branch_inventory_ledger(tenant_id=tenant_id, branch_id=branch_id)
        products_by_id = {
            product.id: product
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }
        records: list[dict[str, object]] = []
        for entry in entries:
            if entry.entry_type not in SUPPORTED_LEDGER_ENTRY_TYPES:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unsupported ledger entry type stored")
            product = products_by_id.get(entry.product_id)
            records.append(
                {
                    "inventory_ledger_entry_id": entry.id,
                    "branch_id": entry.branch_id,
                    "product_id": entry.product_id,
                    "product_name": product.name if product is not None else entry.product_id,
                    "sku_code": product.sku_code if product is not None else entry.product_id,
                    "entry_type": entry.entry_type,
                    "quantity": round(entry.quantity, 2),
                    "reference_type": entry.reference_type,
                    "reference_id": entry.reference_id,
                }
            )
        return records

    async def inventory_snapshot(self, *, tenant_id: str, branch_id: str) -> dict[str, object]:
        ledger = await self.inventory_ledger(tenant_id=tenant_id, branch_id=branch_id)
        products_by_id = {
            product.id: {
                "product_id": product.id,
                "product_name": product.name,
                "sku_code": product.sku_code,
            }
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }
        return build_inventory_snapshot(
            branch_id=branch_id,
            inventory_ledger=ledger,
            products_by_id=products_by_id,
        )

    async def replenishment_board(self, *, tenant_id: str, branch_id: str) -> dict[str, object]:
        await self._assert_branch_exists(tenant_id=tenant_id, branch_id=branch_id)
        snapshot = await self.inventory_snapshot(tenant_id=tenant_id, branch_id=branch_id)
        stock_by_product_id = {
            str(record["product_id"]): float(record["stock_on_hand"])
            for record in snapshot["records"]
        }
        products_by_id = {
            product.id: product
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }
        branch_catalog_items = await self._catalog_repo.list_branch_catalog_items(tenant_id=tenant_id, branch_id=branch_id)
        return build_replenishment_board(
            branch_id=branch_id,
            branch_catalog_items=[
                {
                    "product_id": item.product_id,
                    "product_name": products_by_id[item.product_id].name if item.product_id in products_by_id else item.product_id,
                    "sku_code": products_by_id[item.product_id].sku_code if item.product_id in products_by_id else item.product_id,
                    "availability_status": item.availability_status,
                    "reorder_point": item.reorder_point,
                    "target_stock": item.target_stock,
                }
                for item in branch_catalog_items
            ],
            stock_by_product_id=stock_by_product_id,
        )

    async def create_restock_task(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        product_id: str,
        requested_quantity: float,
        source_posture: str,
        note: str | None,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        await self._assert_product_on_branch(tenant_id=tenant_id, branch_id=branch_id, product_id=product_id)
        branch_catalog_items = await self._catalog_repo.list_branch_catalog_items(tenant_id=tenant_id, branch_id=branch_id)
        branch_catalog_item = next((item for item in branch_catalog_items if item.product_id == product_id), None)
        if branch_catalog_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch catalog item not found")
        if branch_catalog_item.reorder_point is None or branch_catalog_item.target_stock is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Replenishment policy not configured for product")
        if source_posture not in SUPPORTED_RESTOCK_SOURCE_POSTURES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported restock source posture")

        existing_active_task = await self._inventory_repo.get_active_restock_task_for_product(
            tenant_id=tenant_id,
            branch_id=branch_id,
            product_id=product_id,
        )
        try:
            ensure_restock_task_creatable(
                requested_quantity=requested_quantity,
                existing_active_task={"restock_task_id": existing_active_task.id} if existing_active_task is not None else None,
            )
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        stock_on_hand = await self._inventory_repo.stock_on_hand(
            tenant_id=tenant_id,
            branch_id=branch_id,
            product_id=product_id,
        )
        reorder_point_snapshot = float(branch_catalog_item.reorder_point)
        target_stock_snapshot = float(branch_catalog_item.target_stock)
        suggested_quantity_snapshot = max(target_stock_snapshot - stock_on_hand, 0.0)
        sequence_number = await self._inventory_repo.next_branch_restock_task_sequence(
            tenant_id=tenant_id,
            branch_id=branch_id,
        )
        session = await self._inventory_repo.create_restock_task_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            product_id=product_id,
            task_number=restock_task_number(branch_code=branch.code, sequence_number=sequence_number),
            stock_on_hand_snapshot=stock_on_hand,
            reorder_point_snapshot=reorder_point_snapshot,
            target_stock_snapshot=target_stock_snapshot,
            suggested_quantity_snapshot=suggested_quantity_snapshot,
            requested_quantity=requested_quantity,
            source_posture=source_posture,
            note=note,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="restock_task.created",
            entity_type="restock_task_session",
            entity_id=session.id,
            payload={
                "product_id": product_id,
                "task_number": session.task_number,
                "requested_quantity": session.requested_quantity,
                "source_posture": session.source_posture,
            },
        )
        await self._session.commit()
        return self._serialize_restock_task_session(session)

    async def pick_restock_task(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        restock_task_id: str,
        picked_quantity: float,
        note: str | None,
    ) -> dict[str, object]:
        session = await self._inventory_repo.get_restock_task_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            restock_task_id=restock_task_id,
        )
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restock task not found")
        try:
            ensure_restock_task_pickable(
                status=session.status,
                requested_quantity=session.requested_quantity,
                picked_quantity=picked_quantity,
            )
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        session.status = "PICKED"
        session.picked_quantity = picked_quantity
        if session.note is None and note is not None:
            session.note = note
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="restock_task.picked",
            entity_type="restock_task_session",
            entity_id=session.id,
            payload={"product_id": session.product_id, "picked_quantity": session.picked_quantity},
        )
        await self._session.commit()
        return self._serialize_restock_task_session(session)

    async def complete_restock_task(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        restock_task_id: str,
        completion_note: str | None,
    ) -> dict[str, object]:
        session = await self._inventory_repo.get_restock_task_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            restock_task_id=restock_task_id,
        )
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restock task not found")
        try:
            ensure_restock_task_completable(status=session.status)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        session.status = "COMPLETED"
        session.completion_note = completion_note
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="restock_task.completed",
            entity_type="restock_task_session",
            entity_id=session.id,
            payload={"product_id": session.product_id, "picked_quantity": session.picked_quantity},
        )
        await self._session.commit()
        return self._serialize_restock_task_session(session)

    async def cancel_restock_task(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        restock_task_id: str,
        cancel_note: str | None,
    ) -> dict[str, object]:
        session = await self._inventory_repo.get_restock_task_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            restock_task_id=restock_task_id,
        )
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restock task not found")
        try:
            ensure_restock_task_cancelable(status=session.status)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        session.status = "CANCELED"
        session.completion_note = cancel_note
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="restock_task.canceled",
            entity_type="restock_task_session",
            entity_id=session.id,
            payload={"product_id": session.product_id},
        )
        await self._session.commit()
        return self._serialize_restock_task_session(session)

    async def restock_board(self, *, tenant_id: str, branch_id: str) -> dict[str, object]:
        await self._assert_branch_exists(tenant_id=tenant_id, branch_id=branch_id)
        sessions = await self._inventory_repo.list_branch_restock_task_sessions(tenant_id=tenant_id, branch_id=branch_id)
        products_by_id = {
            product.id: {"product_name": product.name, "sku_code": product.sku_code}
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }
        return build_restock_board(
            branch_id=branch_id,
            task_sessions=[
                {
                    "restock_task_id": session.id,
                    "task_number": session.task_number,
                    "product_id": session.product_id,
                    "status": session.status,
                    "stock_on_hand_snapshot": session.stock_on_hand_snapshot,
                    "reorder_point_snapshot": session.reorder_point_snapshot,
                    "target_stock_snapshot": session.target_stock_snapshot,
                    "suggested_quantity_snapshot": session.suggested_quantity_snapshot,
                    "requested_quantity": session.requested_quantity,
                    "picked_quantity": session.picked_quantity,
                    "source_posture": session.source_posture,
                    "note": session.note,
                    "completion_note": session.completion_note,
                }
                for session in sessions
            ],
            products_by_id=products_by_id,
        )

    async def create_stock_adjustment(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        product_id: str,
        quantity_delta: float,
        reason: str,
        note: str | None,
    ) -> dict[str, object]:
        await self._assert_product_on_branch(tenant_id=tenant_id, branch_id=branch_id, product_id=product_id)
        try:
            ensure_stock_adjustment_allowed(quantity_delta=quantity_delta)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        adjustment = await self._inventory_repo.create_stock_adjustment(
            tenant_id=tenant_id,
            branch_id=branch_id,
            product_id=product_id,
            quantity_delta=quantity_delta,
            reason=reason,
            note=note,
        )
        await self._inventory_repo.create_inventory_ledger_entries(
            entries=[
                {
                    "tenant_id": tenant_id,
                    "branch_id": branch_id,
                    "product_id": product_id,
                    "entry_type": "ADJUSTMENT",
                    "quantity": quantity_delta,
                    "reference_type": "stock_adjustment",
                    "reference_id": adjustment.id,
                }
            ]
        )
        resulting_stock = round(
            await self._inventory_repo.stock_on_hand(tenant_id=tenant_id, branch_id=branch_id, product_id=product_id),
            2,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="stock_adjustment.created",
            entity_type="stock_adjustment",
            entity_id=adjustment.id,
            payload={"product_id": product_id, "quantity_delta": quantity_delta, "reason": reason},
        )
        await self._session.commit()
        return {
            "id": adjustment.id,
            "tenant_id": adjustment.tenant_id,
            "branch_id": adjustment.branch_id,
            "product_id": adjustment.product_id,
            "quantity_delta": round(adjustment.quantity_delta, 2),
            "reason": adjustment.reason,
            "note": adjustment.note,
            "resulting_stock_on_hand": resulting_stock,
        }

    async def create_stock_count(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        product_id: str,
        counted_quantity: float,
        note: str | None,
    ) -> dict[str, object]:
        await self._assert_product_on_branch(tenant_id=tenant_id, branch_id=branch_id, product_id=product_id)
        expected_quantity = await self._inventory_repo.stock_on_hand(
            tenant_id=tenant_id,
            branch_id=branch_id,
            product_id=product_id,
        )
        result = build_stock_count_result(expected_quantity=expected_quantity, counted_quantity=counted_quantity)
        count_session = await self._inventory_repo.create_stock_count_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            product_id=product_id,
            counted_quantity=result.counted_quantity,
            expected_quantity=result.expected_quantity,
            variance_quantity=result.variance_quantity,
            note=note,
        )
        if result.variance_quantity != 0:
            await self._inventory_repo.create_inventory_ledger_entries(
                entries=[
                    {
                        "tenant_id": tenant_id,
                        "branch_id": branch_id,
                        "product_id": product_id,
                        "entry_type": "COUNT_VARIANCE",
                        "quantity": result.variance_quantity,
                        "reference_type": "stock_count",
                        "reference_id": count_session.id,
                    }
                ]
            )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="stock_count.recorded",
            entity_type="stock_count_session",
            entity_id=count_session.id,
            payload={"product_id": product_id, "variance_quantity": result.variance_quantity},
        )
        await self._session.commit()
        return {
            "id": count_session.id,
            "tenant_id": count_session.tenant_id,
            "branch_id": count_session.branch_id,
            "product_id": count_session.product_id,
            "counted_quantity": count_session.counted_quantity,
            "expected_quantity": count_session.expected_quantity,
            "variance_quantity": count_session.variance_quantity,
            "note": count_session.note,
            "closing_stock": result.closing_stock,
        }

    async def create_stock_count_review_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        product_id: str,
        note: str | None,
    ) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        await self._assert_product_on_branch(tenant_id=tenant_id, branch_id=branch_id, product_id=product_id)
        expected_quantity = await self._inventory_repo.stock_on_hand(
            tenant_id=tenant_id,
            branch_id=branch_id,
            product_id=product_id,
        )
        sequence_number = await self._inventory_repo.next_branch_stock_count_review_sequence(
            tenant_id=tenant_id,
            branch_id=branch_id,
        )
        session = await self._inventory_repo.create_stock_count_review_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            product_id=product_id,
            session_number=stock_count_session_number(branch_code=branch.code, sequence_number=sequence_number),
            expected_quantity=expected_quantity,
            note=note,
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="stock_count_session.created",
            entity_type="stock_count_review_session",
            entity_id=session.id,
            payload={"product_id": product_id, "session_number": session.session_number},
        )
        await self._session.commit()
        return self._serialize_stock_count_review_session(session)

    async def record_stock_count_review_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        stock_count_session_id: str,
        counted_quantity: float,
        note: str | None,
    ) -> dict[str, object]:
        session = await self._inventory_repo.get_stock_count_review_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            stock_count_session_id=stock_count_session_id,
        )
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock count session not found")
        try:
            ensure_stock_count_review_recordable(status=session.status)
            result = build_stock_count_result(expected_quantity=session.expected_quantity, counted_quantity=counted_quantity)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        session.counted_quantity = result.counted_quantity
        session.variance_quantity = result.variance_quantity
        session.status = "COUNTED"
        session.note = note or session.note
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="stock_count_session.counted",
            entity_type="stock_count_review_session",
            entity_id=session.id,
            payload={"product_id": session.product_id, "variance_quantity": result.variance_quantity},
        )
        await self._session.commit()
        return self._serialize_stock_count_review_session(session)

    async def approve_stock_count_review_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        stock_count_session_id: str,
        review_note: str | None,
    ) -> dict[str, object]:
        session = await self._inventory_repo.get_stock_count_review_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            stock_count_session_id=stock_count_session_id,
        )
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock count session not found")
        try:
            ensure_stock_count_review_approvable(status=session.status)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        count_session = await self._inventory_repo.create_stock_count_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            product_id=session.product_id,
            counted_quantity=float(session.counted_quantity or 0.0),
            expected_quantity=session.expected_quantity,
            variance_quantity=float(session.variance_quantity or 0.0),
            note=session.note,
        )
        if money := float(session.variance_quantity or 0.0):
            if money != 0:
                await self._inventory_repo.create_inventory_ledger_entries(
                    entries=[
                        {
                            "tenant_id": tenant_id,
                            "branch_id": branch_id,
                            "product_id": session.product_id,
                            "entry_type": "COUNT_VARIANCE",
                            "quantity": money,
                            "reference_type": "stock_count",
                            "reference_id": count_session.id,
                        }
                    ]
                )
        session.status = "APPROVED"
        session.review_note = review_note
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="stock_count_session.approved",
            entity_type="stock_count_review_session",
            entity_id=session.id,
            payload={"product_id": session.product_id, "variance_quantity": session.variance_quantity},
        )
        await self._session.commit()
        return {
            "session": self._serialize_stock_count_review_session(session),
            "stock_count": {
                "id": count_session.id,
                "tenant_id": count_session.tenant_id,
                "branch_id": count_session.branch_id,
                "product_id": count_session.product_id,
                "counted_quantity": count_session.counted_quantity,
                "expected_quantity": count_session.expected_quantity,
                "variance_quantity": count_session.variance_quantity,
                "note": count_session.note,
                "closing_stock": round(count_session.expected_quantity + count_session.variance_quantity, 2),
            },
        }

    async def cancel_stock_count_review_session(
        self,
        *,
        tenant_id: str,
        branch_id: str,
        actor_user_id: str,
        stock_count_session_id: str,
        review_note: str | None,
    ) -> dict[str, object]:
        session = await self._inventory_repo.get_stock_count_review_session(
            tenant_id=tenant_id,
            branch_id=branch_id,
            stock_count_session_id=stock_count_session_id,
        )
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock count session not found")
        try:
            ensure_stock_count_review_cancelable(status=session.status)
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
        session.status = "CANCELED"
        session.review_note = review_note
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            action="stock_count_session.canceled",
            entity_type="stock_count_review_session",
            entity_id=session.id,
            payload={"product_id": session.product_id},
        )
        await self._session.commit()
        return self._serialize_stock_count_review_session(session)

    async def stock_count_board(self, *, tenant_id: str, branch_id: str) -> dict[str, object]:
        await self._assert_branch_exists(tenant_id=tenant_id, branch_id=branch_id)
        sessions = await self._inventory_repo.list_branch_stock_count_review_sessions(tenant_id=tenant_id, branch_id=branch_id)
        products_by_id = {
            product.id: {"product_name": product.name, "sku_code": product.sku_code}
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }
        return build_stock_count_board(
            branch_id=branch_id,
            review_sessions=[
                {
                    "stock_count_session_id": session.id,
                    "session_number": session.session_number,
                    "product_id": session.product_id,
                    "status": session.status,
                    "expected_quantity": session.expected_quantity,
                    "counted_quantity": session.counted_quantity,
                    "variance_quantity": session.variance_quantity,
                    "note": session.note,
                    "review_note": session.review_note,
                }
                for session in sessions
            ],
            products_by_id=products_by_id,
        )

    async def create_transfer(
        self,
        *,
        tenant_id: str,
        source_branch_id: str,
        actor_user_id: str,
        destination_branch_id: str,
        product_id: str,
        quantity: float,
        note: str | None,
    ) -> dict[str, object]:
        source_branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=source_branch_id)
        destination_branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=destination_branch_id)
        if source_branch is None or destination_branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        await self._assert_product_on_branch(tenant_id=tenant_id, branch_id=source_branch_id, product_id=product_id)
        available_quantity = await self._inventory_repo.stock_on_hand(
            tenant_id=tenant_id,
            branch_id=source_branch_id,
            product_id=product_id,
        )
        try:
            ensure_transfer_allowed(
                source_branch_id=source_branch_id,
                destination_branch_id=destination_branch_id,
                quantity=quantity,
                available_quantity=available_quantity,
            )
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

        sequence_number = await self._inventory_repo.next_branch_transfer_sequence(
            tenant_id=tenant_id,
            source_branch_id=source_branch_id,
        )
        transfer = await self._inventory_repo.create_transfer_order(
            tenant_id=tenant_id,
            source_branch_id=source_branch_id,
            destination_branch_id=destination_branch_id,
            product_id=product_id,
            transfer_number=transfer_number(branch_code=source_branch.code, sequence_number=sequence_number),
            quantity=quantity,
            note=note,
        )
        await self._inventory_repo.create_inventory_ledger_entries(
            entries=[
                {
                    "tenant_id": tenant_id,
                    "branch_id": source_branch_id,
                    "product_id": product_id,
                    "entry_type": "TRANSFER_OUT",
                    "quantity": -abs(quantity),
                    "reference_type": "transfer_order",
                    "reference_id": transfer.id,
                },
                {
                    "tenant_id": tenant_id,
                    "branch_id": destination_branch_id,
                    "product_id": product_id,
                    "entry_type": "TRANSFER_IN",
                    "quantity": abs(quantity),
                    "reference_type": "transfer_order",
                    "reference_id": transfer.id,
                },
            ]
        )
        await self._audit_repo.record(
            tenant_id=tenant_id,
            branch_id=source_branch_id,
            actor_user_id=actor_user_id,
            action="transfer.created",
            entity_type="transfer_order",
            entity_id=transfer.id,
            payload={"product_id": product_id, "destination_branch_id": destination_branch_id, "quantity": quantity},
        )
        await self._session.commit()
        return {
            "id": transfer.id,
            "tenant_id": transfer.tenant_id,
            "source_branch_id": transfer.source_branch_id,
            "destination_branch_id": transfer.destination_branch_id,
            "product_id": transfer.product_id,
            "transfer_number": transfer.transfer_number,
            "quantity": round(transfer.quantity, 2),
            "status": transfer.status,
            "note": transfer.note,
        }

    async def transfer_board(self, *, tenant_id: str, branch_id: str) -> dict[str, object]:
        await self._assert_branch_exists(tenant_id=tenant_id, branch_id=branch_id)
        transfers = await self._inventory_repo.list_branch_transfers(tenant_id=tenant_id, branch_id=branch_id)
        branches = {
            branch.id: {"name": branch.name}
            for branch in await self._tenant_repo.list_branches(tenant_id)
        }
        products = {
            product.id: {"product_name": product.name, "sku_code": product.sku_code}
            for product in await self._catalog_repo.list_products(tenant_id=tenant_id)
        }
        return build_transfer_board(
            branch_id=branch_id,
            transfers=[
                {
                    "transfer_order_id": transfer.id,
                    "transfer_number": transfer.transfer_number,
                    "source_branch_id": transfer.source_branch_id,
                    "destination_branch_id": transfer.destination_branch_id,
                    "product_id": transfer.product_id,
                    "quantity": transfer.quantity,
                    "status": transfer.status,
                }
                for transfer in transfers
            ],
            branches_by_id=branches,
            products_by_id=products,
        )

    async def _assert_branch_exists(self, *, tenant_id: str, branch_id: str) -> None:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

    async def _assert_product_on_branch(self, *, tenant_id: str, branch_id: str, product_id: str) -> None:
        await self._assert_branch_exists(tenant_id=tenant_id, branch_id=branch_id)
        product = await self._catalog_repo.get_product(tenant_id=tenant_id, product_id=product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catalog product not found")

    async def _build_purchase_order_records(self, *, tenant_id: str, branch_id: str) -> list[dict[str, object]]:
        purchase_orders = await self._purchasing_repo.list_branch_purchase_orders(tenant_id=tenant_id, branch_id=branch_id)
        lines_by_order_id = await self._purchasing_repo.list_purchase_order_lines_for_orders(
            purchase_order_ids=[purchase_order.id for purchase_order in purchase_orders]
        )
        suppliers = {
            supplier.id: supplier
            for supplier in await self._purchasing_repo.list_suppliers(tenant_id=tenant_id)
        }
        return [
            {
                "purchase_order_id": purchase_order.id,
                "purchase_order_number": purchase_order.purchase_order_number,
                "supplier_id": purchase_order.supplier_id,
                "supplier_name": suppliers[purchase_order.supplier_id].name
                if purchase_order.supplier_id in suppliers
                else purchase_order.supplier_id,
                "approval_status": purchase_order.approval_status,
                "line_count": len(lines_by_order_id.get(purchase_order.id, [])),
                "ordered_quantity": round(
                    sum(line.quantity for line in lines_by_order_id.get(purchase_order.id, [])),
                    2,
                ),
                "grand_total": purchase_order.grand_total,
                "approval_requested_note": purchase_order.approval_requested_note,
                "approval_decision_note": purchase_order.approval_decision_note,
            }
            for purchase_order in purchase_orders
        ]

    def _serialize_stock_count_review_session(self, session) -> dict[str, object]:
        return {
            "id": session.id,
            "tenant_id": session.tenant_id,
            "branch_id": session.branch_id,
            "product_id": session.product_id,
            "session_number": session.session_number,
            "status": session.status,
            "expected_quantity": None if session.status == "OPEN" else session.expected_quantity,
            "counted_quantity": session.counted_quantity,
            "variance_quantity": session.variance_quantity,
            "note": session.note,
            "review_note": session.review_note,
        }

    def _serialize_restock_task_session(self, session) -> dict[str, object]:
        return {
            "id": session.id,
            "tenant_id": session.tenant_id,
            "branch_id": session.branch_id,
            "product_id": session.product_id,
            "task_number": session.task_number,
            "status": session.status,
            "stock_on_hand_snapshot": round(float(session.stock_on_hand_snapshot), 2),
            "reorder_point_snapshot": round(float(session.reorder_point_snapshot), 2),
            "target_stock_snapshot": round(float(session.target_stock_snapshot), 2),
            "suggested_quantity_snapshot": round(float(session.suggested_quantity_snapshot), 2),
            "requested_quantity": round(float(session.requested_quantity), 2),
            "picked_quantity": None if session.picked_quantity is None else round(float(session.picked_quantity), 2),
            "source_posture": session.source_posture,
            "note": session.note,
            "completion_note": session.completion_note,
        }
