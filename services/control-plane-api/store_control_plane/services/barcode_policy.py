from __future__ import annotations


def normalize_barcode(value: str) -> str:
    return "".join(value.split()).strip()


def tenant_code(tenant_name: str) -> str:
    token = "".join(character for character in tenant_name.upper() if character.isalnum())
    return token[:4] or "ITEM"


def sku_code(sku_value: str) -> str:
    return "".join(character for character in sku_value.upper() if character.isalnum())


def allocate_barcode(*, tenant_name: str, sku_value: str, existing: str | None = None) -> str:
    existing_barcode = normalize_barcode(existing or "")
    if existing_barcode:
        return existing_barcode
    return f"{tenant_code(tenant_name)}{sku_code(sku_value)}"[:14]


def build_barcode_label_preview(
    *,
    sku_value: str,
    product_name: str,
    barcode: str,
    selling_price: float,
) -> dict[str, str]:
    return {
        "sku_code": sku_value,
        "product_name": product_name,
        "barcode": normalize_barcode(barcode),
        "price_label": f"Rs. {float(selling_price):.2f}",
    }
