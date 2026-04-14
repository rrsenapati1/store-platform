from __future__ import annotations

from dataclasses import dataclass, field


SUPPORTED_LEDGER_ENTRY_TYPES = {
    "OPENING",
    "PURCHASE_RECEIPT",
    "SALE",
    "SALE_RETURN",
    "TRANSFER_OUT",
    "TRANSFER_IN",
    "ADJUSTMENT",
    "DAMAGE",
    "EXPIRY_WRITE_OFF",
    "CUSTOMER_RETURN",
    "SUPPLIER_RETURN",
    "COUNT_VARIANCE",
}


@dataclass(slots=True)
class InventoryLedgerService:
    entries: list[dict[str, object]] = field(default_factory=list)

    def post_entry(self, *, item_id: str, branch_id: str, quantity: float, entry_type: str) -> dict[str, object]:
        if entry_type not in SUPPORTED_LEDGER_ENTRY_TYPES:
            raise ValueError(f"Unsupported ledger entry type: {entry_type}")
        entry = {
            "item_id": item_id,
            "branch_id": branch_id,
            "quantity": quantity,
            "entry_type": entry_type,
        }
        self.entries.append(entry)
        return entry

    def stock_on_hand(self, *, item_id: str, branch_id: str) -> float:
        return sum(
            float(entry["quantity"])
            for entry in self.entries
            if entry["item_id"] == item_id and entry["branch_id"] == branch_id
        )

    def transfer_stock(
        self,
        *,
        item_id: str,
        source_branch_id: str,
        destination_branch_id: str,
        quantity: float,
    ) -> dict[str, float | str]:
        self.post_entry(
            item_id=item_id,
            branch_id=source_branch_id,
            quantity=-quantity,
            entry_type="TRANSFER_OUT",
        )
        self.post_entry(
            item_id=item_id,
            branch_id=destination_branch_id,
            quantity=quantity,
            entry_type="TRANSFER_IN",
        )
        return {
            "product_id": item_id,
            "quantity": quantity,
            "source_stock_after": self.stock_on_hand(item_id=item_id, branch_id=source_branch_id),
            "destination_stock_after": self.stock_on_hand(item_id=item_id, branch_id=destination_branch_id),
        }

    def apply_stock_count(
        self,
        *,
        item_id: str,
        branch_id: str,
        counted_quantity: float,
    ) -> dict[str, float | str]:
        expected_quantity = self.stock_on_hand(item_id=item_id, branch_id=branch_id)
        variance_quantity = counted_quantity - expected_quantity
        if variance_quantity:
            self.post_entry(
                item_id=item_id,
                branch_id=branch_id,
                quantity=variance_quantity,
                entry_type="COUNT_VARIANCE",
            )
        return {
            "product_id": item_id,
            "expected_quantity": expected_quantity,
            "counted_quantity": counted_quantity,
            "variance_quantity": variance_quantity,
            "closing_stock": self.stock_on_hand(item_id=item_id, branch_id=branch_id),
        }
