from __future__ import annotations

from typing import Any


def normalize_barcode(value: str) -> str:
    return "".join(value.split()).strip()


def _tenant_code(tenant_name: str) -> str:
    token = "".join(character for character in tenant_name.upper() if character.isalnum())
    return token[:4] or "ITEM"


def _sku_code(sku_code: str) -> str:
    return "".join(character for character in sku_code.upper() if character.isalnum())


def allocate_barcode(*, tenant_name: str, sku_code: str, existing: str | None = None) -> str:
    existing_barcode = normalize_barcode(existing or "")
    if existing_barcode:
        return existing_barcode
    return f"{_tenant_code(tenant_name)}{_sku_code(sku_code)}"[:14]


def build_barcode_label_model(
    *,
    sku_code: str,
    product_name: str,
    barcode: str,
    selling_price: float,
) -> dict[str, Any]:
    return {
        "sku_code": sku_code,
        "product_name": product_name,
        "barcode": normalize_barcode(barcode),
        "price_label": f"Rs. {float(selling_price):.2f}",
    }
