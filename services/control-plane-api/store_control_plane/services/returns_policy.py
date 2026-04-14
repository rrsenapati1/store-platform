from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import re
from typing import Any

from .billing_policy import _state_code
from .purchase_policy import money, normalize_gstin


def credit_note_number(*, branch_code: str, sequence_number: int) -> str:
    branch_segment = re.sub(r"[^A-Z0-9]", "", branch_code.upper())
    return f"SCN-{branch_segment}-{sequence_number:04d}"


def ensure_refund_amount_allowed(
    *,
    requested_refund_amount: float,
    credit_note_total: float,
    remaining_refundable_amount: float,
) -> None:
    requested = money(requested_refund_amount)
    if requested > money(remaining_refundable_amount):
        raise ValueError("Refund exceeds remaining sale balance")
    if requested > money(credit_note_total):
        raise ValueError("Refund exceeds credit note value")


@dataclass(slots=True)
class SaleReturnLineDraft:
    product_id: str
    product_name: str
    sku_code: str
    hsn_sac_code: str
    quantity: float
    unit_price: float
    gst_rate: float
    line_subtotal: float
    tax_total: float
    line_total: float


@dataclass(slots=True)
class CreditNoteTaxLineDraft:
    tax_type: str
    tax_rate: float
    taxable_amount: float
    tax_amount: float


@dataclass(slots=True)
class SaleReturnDraft:
    customer_name: str
    customer_gstin: str | None
    subtotal: float
    tax_total: float
    cgst_total: float
    sgst_total: float
    igst_total: float
    grand_total: float
    lines: list[SaleReturnLineDraft]
    tax_lines: list[CreditNoteTaxLineDraft]


def build_sale_return_draft(
    *,
    branch_gstin: str | None,
    sale_customer_name: str,
    sale_customer_gstin: str | None,
    sale_lines_by_product_id: Mapping[str, Any],
    prior_returned_quantities_by_product_id: Mapping[str, float],
    requested_lines: Iterable[Mapping[str, Any]],
) -> SaleReturnDraft:
    normalized_customer_gstin = normalize_gstin(sale_customer_gstin)
    is_inter_state = (
        normalized_customer_gstin is not None
        and _state_code(branch_gstin) is not None
        and _state_code(branch_gstin) != _state_code(normalized_customer_gstin)
    )

    drafts: list[SaleReturnLineDraft] = []
    tax_groups: dict[tuple[str, float], dict[str, float]] = defaultdict(lambda: {"taxable_amount": 0.0, "tax_amount": 0.0})
    subtotal = 0.0
    tax_total = 0.0

    for requested_line in requested_lines:
        product_id = str(requested_line["product_id"])
        if product_id not in sale_lines_by_product_id:
            raise ValueError("Sale line not found for return")

        sale_line = sale_lines_by_product_id[product_id]
        requested_quantity = money(float(requested_line["quantity"]))
        if requested_quantity <= 0:
            raise ValueError("Return quantity must be greater than zero")

        sold_quantity = money(float(sale_line["quantity"]))
        already_returned_quantity = money(float(prior_returned_quantities_by_product_id.get(product_id, 0.0)))
        remaining_quantity = money(sold_quantity - already_returned_quantity)
        if requested_quantity > remaining_quantity:
            raise ValueError("Return quantity exceeds remaining sale quantity")

        unit_price = money(float(sale_line["unit_price"]))
        gst_rate = money(float(sale_line["gst_rate"]))
        line_subtotal = money(requested_quantity * unit_price)
        line_tax_total = money(line_subtotal * gst_rate / 100)
        line_total = money(line_subtotal + line_tax_total)

        drafts.append(
            SaleReturnLineDraft(
                product_id=product_id,
                product_name=str(sale_line["product_name"]),
                sku_code=str(sale_line["sku_code"]),
                hsn_sac_code=str(sale_line["hsn_sac_code"]),
                quantity=requested_quantity,
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
        CreditNoteTaxLineDraft(
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

    return SaleReturnDraft(
        customer_name=sale_customer_name.strip(),
        customer_gstin=normalized_customer_gstin,
        subtotal=money(subtotal),
        tax_total=money(tax_total),
        cgst_total=cgst_total,
        sgst_total=sgst_total,
        igst_total=igst_total,
        grand_total=money(subtotal + tax_total),
        lines=drafts,
        tax_lines=tax_lines,
    )
