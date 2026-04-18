from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import re
from typing import Any

from .purchase_policy import money, normalize_gstin


def sale_invoice_number(*, branch_code: str, sequence_number: int) -> str:
    branch_segment = re.sub(r"[^A-Z0-9]", "", branch_code.upper())
    return f"SINV-{branch_segment}-{sequence_number:04d}"


def ensure_sale_stock_available(*, requested_quantity: float, available_quantity: float) -> None:
    if money(requested_quantity) <= 0:
        raise ValueError("Sale quantity must be greater than zero")
    if money(requested_quantity) > money(available_quantity):
        raise ValueError("Insufficient stock for sale")


def _value(record: Any, field: str):
    if isinstance(record, Mapping):
        return record[field]
    return getattr(record, field)


def _state_code(gstin: str | None) -> str | None:
    normalized = normalize_gstin(gstin)
    if normalized is None or len(normalized) < 2:
        return None
    return normalized[:2]


@dataclass(slots=True)
class SaleLineDraft:
    product_id: str
    product_name: str
    sku_code: str
    hsn_sac_code: str
    quantity: float
    serial_numbers: list[str]
    compliance_profile: str
    compliance_capture: dict[str, object]
    unit_price: float
    gst_rate: float
    line_subtotal: float
    tax_total: float
    line_total: float


@dataclass(slots=True)
class TaxLineDraft:
    tax_type: str
    tax_rate: float
    taxable_amount: float
    tax_amount: float


@dataclass(slots=True)
class SaleDraft:
    customer_name: str
    customer_gstin: str | None
    invoice_kind: str
    irn_status: str
    subtotal: float
    tax_total: float
    cgst_total: float
    sgst_total: float
    igst_total: float
    grand_total: float
    lines: list[SaleLineDraft]
    tax_lines: list[TaxLineDraft]


def build_sale_draft(
    *,
    line_inputs: Iterable[Mapping[str, Any]],
    branch_gstin: str | None,
    customer_name: str,
    customer_gstin: str | None,
    products_by_id: Mapping[str, Any],
    branch_catalog_items_by_product_id: Mapping[str, Any],
) -> SaleDraft:
    normalized_customer_gstin = normalize_gstin(customer_gstin)
    invoice_kind = "B2B" if normalized_customer_gstin else "B2C"
    irn_status = "IRN_PENDING" if invoice_kind == "B2B" else "NOT_REQUIRED"
    is_inter_state = (
        normalized_customer_gstin is not None
        and _state_code(branch_gstin) is not None
        and _state_code(branch_gstin) != _state_code(normalized_customer_gstin)
    )

    drafts: list[SaleLineDraft] = []
    tax_groups: dict[tuple[str, float], dict[str, float]] = defaultdict(lambda: {"taxable_amount": 0.0, "tax_amount": 0.0})
    subtotal = 0.0
    tax_total = 0.0

    for line_input in line_inputs:
        product_id = str(line_input["product_id"])
        if product_id not in products_by_id:
            raise ValueError("Catalog product not found for sale")
        if product_id not in branch_catalog_items_by_product_id:
            raise ValueError("Branch catalog item not found for sale")

        product = products_by_id[product_id]
        catalog_item = branch_catalog_items_by_product_id[product_id]
        availability_status = str(_value(catalog_item, "availability_status")).upper()
        if availability_status != "ACTIVE":
            raise ValueError("Branch catalog item is not active")

        quantity = money(float(line_input["quantity"]))
        if quantity <= 0:
            raise ValueError("Sale quantity must be greater than zero")

        unit_price = money(float(_value(catalog_item, "effective_selling_price")))
        gst_rate = money(float(_value(product, "gst_rate")))
        line_subtotal = money(quantity * unit_price)
        line_tax_total = money(line_subtotal * gst_rate / 100)
        line_total = money(line_subtotal + line_tax_total)

        drafts.append(
            SaleLineDraft(
                product_id=product_id,
                product_name=str(_value(product, "name")),
                sku_code=str(_value(product, "sku_code")),
                hsn_sac_code=str(_value(product, "hsn_sac_code")),
                quantity=quantity,
                serial_numbers=list(line_input.get("serial_numbers") or []),
                compliance_profile=str(_value(product, "compliance_profile") or "NONE"),
                compliance_capture=dict(line_input.get("compliance_capture") or {}),
                unit_price=unit_price,
                gst_rate=gst_rate,
                line_subtotal=line_subtotal,
                tax_total=line_tax_total,
                line_total=line_total,
            )
        )

        subtotal += line_subtotal
        tax_total += line_tax_total

        if is_inter_state:
            key = ("IGST", gst_rate)
            tax_groups[key]["taxable_amount"] = money(tax_groups[key]["taxable_amount"] + line_subtotal)
            tax_groups[key]["tax_amount"] = money(tax_groups[key]["tax_amount"] + line_tax_total)
        else:
            split_rate = money(gst_rate / 2)
            cgst_amount = money(line_tax_total / 2)
            sgst_amount = money(line_tax_total - cgst_amount)
            for tax_type, amount in (("CGST", cgst_amount), ("SGST", sgst_amount)):
                key = (tax_type, split_rate)
                tax_groups[key]["taxable_amount"] = money(tax_groups[key]["taxable_amount"] + line_subtotal)
                tax_groups[key]["tax_amount"] = money(tax_groups[key]["tax_amount"] + amount)

    tax_lines = [
        TaxLineDraft(
            tax_type=tax_type,
            tax_rate=tax_rate,
            taxable_amount=money(group["taxable_amount"]),
            tax_amount=money(group["tax_amount"]),
        )
        for (tax_type, tax_rate), group in sorted(tax_groups.items(), key=lambda item: (item[0][0], item[0][1]))
    ]
    cgst_total = money(sum(line.tax_amount for line in tax_lines if line.tax_type == "CGST"))
    sgst_total = money(sum(line.tax_amount for line in tax_lines if line.tax_type == "SGST"))
    igst_total = money(sum(line.tax_amount for line in tax_lines if line.tax_type == "IGST"))

    return SaleDraft(
        customer_name=customer_name.strip(),
        customer_gstin=normalized_customer_gstin,
        invoice_kind=invoice_kind,
        irn_status=irn_status,
        subtotal=money(subtotal),
        tax_total=money(tax_total),
        cgst_total=cgst_total,
        sgst_total=sgst_total,
        igst_total=igst_total,
        grand_total=money(subtotal + tax_total),
        lines=drafts,
        tax_lines=tax_lines,
    )
