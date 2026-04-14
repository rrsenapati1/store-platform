from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def _money(value: float) -> float:
    return round(float(value), 2)


def build_central_catalog_records(*, products: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    records = [
        {
            "product_id": product["id"],
            "product_name": product["name"],
            "sku_code": product["sku_code"],
            "barcode": str(product["barcode"]),
            "selling_price": _money(product["selling_price"]),
            "tax_rate_percent": _money(product["tax_rate_percent"]),
            "hsn_sac_code": product["hsn_sac_code"],
        }
        for product in products
    ]
    return sorted(records, key=lambda record: (record["product_name"], record["sku_code"]))


def build_branch_catalog_records(
    *,
    products: Iterable[dict[str, Any]],
    catalog_overrides: Mapping[tuple[str, str], dict[str, Any]],
    branch_id: str,
    stock_by_product: Mapping[str, float],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for product in products:
        product_id = product["id"]
        override = catalog_overrides.get((branch_id, product_id))
        is_active = True if override is None else bool(override["is_active"])
        uses_override_price = override is not None and override.get("selling_price") is not None
        selling_price = override["selling_price"] if uses_override_price else product["selling_price"]
        stock_on_hand = _money(stock_by_product.get(product_id, 0.0))
        availability_status = "AVAILABLE"
        if not is_active:
            availability_status = "INACTIVE"
        elif stock_on_hand <= 0:
            availability_status = "OUT_OF_STOCK"
        elif stock_on_hand <= 5:
            availability_status = "LOW_STOCK"

        records.append(
            {
                "product_id": product_id,
                "product_name": product["name"],
                "sku_code": product["sku_code"],
                "barcode": str(product["barcode"]),
                "hsn_sac_code": product["hsn_sac_code"],
                "selling_price": _money(selling_price),
                "stock_on_hand": stock_on_hand,
                "is_active": is_active,
                "price_source": "OVERRIDE" if uses_override_price else "MASTER",
                "availability_status": availability_status,
            }
        )
    return sorted(records, key=lambda record: (record["product_name"], record["sku_code"]))


def build_inventory_snapshot_report(*, catalog_records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    records = [
        {
            "product_id": record["product_id"],
            "product_name": record["product_name"],
            "stock_on_hand": _money(record["stock_on_hand"]),
            "availability_status": record["availability_status"],
        }
        for record in catalog_records
    ]
    return {
        "sku_count": len(records),
        "low_stock_count": sum(1 for record in records if record["availability_status"] == "LOW_STOCK"),
        "out_of_stock_count": sum(1 for record in records if record["availability_status"] == "OUT_OF_STOCK"),
        "inactive_count": sum(1 for record in records if record["availability_status"] == "INACTIVE"),
        "records": records,
    }
