from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

from .purchase_policy import money, normalize_gstin


def _state_code(gstin: str | None) -> str | None:
    normalized = normalize_gstin(gstin)
    if normalized is None or len(normalized) < 2:
        return None
    return normalized[:2]


def _fiscal_year_code(as_of: date) -> str:
    if as_of.month >= 4:
        start_year = as_of.year
        end_year = as_of.year + 1
    else:
        start_year = as_of.year - 1
        end_year = as_of.year
    return f"{start_year % 100:02d}{end_year % 100:02d}"


def purchase_invoice_number(*, branch_code: str, issued_on: date, sequence_number: int) -> str:
    return f"SPINV-{_fiscal_year_code(issued_on)}-{sequence_number:06d}"


def supplier_credit_note_number(*, branch_code: str, issued_on: date, sequence_number: int) -> str:
    return f"SRCN-{_fiscal_year_code(issued_on)}-{sequence_number:06d}"


def supplier_payment_number(*, branch_code: str, paid_on: date, sequence_number: int) -> str:
    return f"SPAY-{_fiscal_year_code(paid_on)}-{sequence_number:06d}"


@dataclass(slots=True)
class ProcurementTaxLineDraft:
    tax_type: str
    tax_rate: float
    taxable_amount: float
    tax_amount: float


@dataclass(slots=True)
class PurchaseInvoiceLineDraft:
    product_id: str
    product_name: str
    sku_code: str
    quantity: float
    unit_cost: float
    gst_rate: float
    line_subtotal: float
    tax_total: float
    line_total: float


@dataclass(slots=True)
class PurchaseInvoiceDraft:
    subtotal: float
    cgst_total: float
    sgst_total: float
    igst_total: float
    grand_total: float
    lines: list[PurchaseInvoiceLineDraft]
    tax_lines: list[ProcurementTaxLineDraft]


def _build_procurement_tax_lines(
    *,
    line_inputs: Iterable[tuple[float, float]],
    seller_gstin: str | None,
    buyer_gstin: str | None,
) -> tuple[list[ProcurementTaxLineDraft], float, float, float]:
    tax_groups: dict[tuple[str, float], dict[str, float]] = defaultdict(lambda: {"taxable_amount": 0.0, "tax_amount": 0.0})
    is_inter_state = (
        _state_code(seller_gstin) is not None
        and _state_code(buyer_gstin) is not None
        and _state_code(seller_gstin) != _state_code(buyer_gstin)
    )

    for taxable_amount, gst_rate in line_inputs:
        line_tax_total = money(taxable_amount * gst_rate / 100)
        if is_inter_state:
            key = ("IGST", gst_rate)
            tax_groups[key]["taxable_amount"] = money(tax_groups[key]["taxable_amount"] + taxable_amount)
            tax_groups[key]["tax_amount"] = money(tax_groups[key]["tax_amount"] + line_tax_total)
            continue

        split_rate = money(gst_rate / 2)
        cgst_amount = money(line_tax_total / 2)
        sgst_amount = money(line_tax_total - cgst_amount)
        for tax_type, tax_amount in (("CGST", cgst_amount), ("SGST", sgst_amount)):
            key = (tax_type, split_rate)
            tax_groups[key]["taxable_amount"] = money(tax_groups[key]["taxable_amount"] + taxable_amount)
            tax_groups[key]["tax_amount"] = money(tax_groups[key]["tax_amount"] + tax_amount)

    tax_lines = [
        ProcurementTaxLineDraft(
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
    return tax_lines, cgst_total, sgst_total, igst_total


def build_purchase_invoice_draft(
    *,
    goods_receipt_lines: Iterable[Mapping[str, Any]],
    products_by_id: Mapping[str, Any],
    supplier_gstin: str | None,
    branch_gstin: str | None,
) -> PurchaseInvoiceDraft:
    drafts: list[PurchaseInvoiceLineDraft] = []
    tax_inputs: list[tuple[float, float]] = []
    subtotal = 0.0

    for goods_receipt_line in goods_receipt_lines:
        product_id = str(goods_receipt_line["product_id"])
        product = products_by_id[product_id]
        quantity = money(float(goods_receipt_line["quantity"]))
        if quantity <= 0:
            continue
        unit_cost = money(float(goods_receipt_line["unit_cost"]))
        gst_rate = money(float(product.gst_rate))
        line_subtotal = money(quantity * unit_cost)
        line_tax_total = money(line_subtotal * gst_rate / 100)
        line_total = money(line_subtotal + line_tax_total)
        subtotal = money(subtotal + line_subtotal)
        tax_inputs.append((line_subtotal, gst_rate))
        drafts.append(
            PurchaseInvoiceLineDraft(
                product_id=product_id,
                product_name=product.name,
                sku_code=product.sku_code,
                quantity=quantity,
                unit_cost=unit_cost,
                gst_rate=gst_rate,
                line_subtotal=line_subtotal,
                tax_total=line_tax_total,
                line_total=line_total,
            )
        )

    tax_lines, cgst_total, sgst_total, igst_total = _build_procurement_tax_lines(
        line_inputs=tax_inputs,
        seller_gstin=supplier_gstin,
        buyer_gstin=branch_gstin,
    )
    return PurchaseInvoiceDraft(
        subtotal=subtotal,
        cgst_total=cgst_total,
        sgst_total=sgst_total,
        igst_total=igst_total,
        grand_total=money(subtotal + cgst_total + sgst_total + igst_total),
        lines=drafts,
        tax_lines=tax_lines,
    )


def ensure_purchase_invoice_not_already_created(*, goods_receipt_id: str, existing_purchase_invoice: Any | None) -> None:
    if existing_purchase_invoice is not None:
        raise ValueError("Purchase invoice already exists for goods receipt")


def build_supplier_return_draft(
    *,
    invoice_lines_by_product_id: Mapping[str, Mapping[str, Any]],
    prior_returned_quantities_by_product_id: Mapping[str, float],
    requested_lines: Iterable[Mapping[str, Any]],
    supplier_gstin: str | None,
    branch_gstin: str | None,
) -> PurchaseInvoiceDraft:
    drafts: list[PurchaseInvoiceLineDraft] = []
    tax_inputs: list[tuple[float, float]] = []
    subtotal = 0.0

    for requested_line in requested_lines:
        product_id = str(requested_line["product_id"])
        if product_id not in invoice_lines_by_product_id:
            raise ValueError("Purchase invoice line not found for supplier return")
        invoice_line = invoice_lines_by_product_id[product_id]
        quantity = money(float(requested_line["quantity"]))
        if quantity <= 0:
            raise ValueError("Supplier return quantity must be greater than zero")
        available_quantity = money(float(invoice_line["quantity"]) - float(prior_returned_quantities_by_product_id.get(product_id, 0.0)))
        if quantity > available_quantity:
            raise ValueError("Supplier return quantity exceeds available invoice quantity")

        unit_cost = money(float(invoice_line["unit_cost"]))
        gst_rate = money(float(invoice_line["gst_rate"]))
        line_subtotal = money(quantity * unit_cost)
        line_tax_total = money(line_subtotal * gst_rate / 100)
        line_total = money(line_subtotal + line_tax_total)
        subtotal = money(subtotal + line_subtotal)
        tax_inputs.append((line_subtotal, gst_rate))
        drafts.append(
            PurchaseInvoiceLineDraft(
                product_id=product_id,
                product_name=str(invoice_line["product_name"]),
                sku_code=str(invoice_line["sku_code"]),
                quantity=quantity,
                unit_cost=unit_cost,
                gst_rate=gst_rate,
                line_subtotal=line_subtotal,
                tax_total=line_tax_total,
                line_total=line_total,
            )
        )

    tax_lines, cgst_total, sgst_total, igst_total = _build_procurement_tax_lines(
        line_inputs=tax_inputs,
        seller_gstin=supplier_gstin,
        buyer_gstin=branch_gstin,
    )
    return PurchaseInvoiceDraft(
        subtotal=subtotal,
        cgst_total=cgst_total,
        sgst_total=sgst_total,
        igst_total=igst_total,
        grand_total=money(subtotal + cgst_total + sgst_total + igst_total),
        lines=drafts,
        tax_lines=tax_lines,
    )


def ensure_supplier_payment_within_outstanding(
    *,
    invoice_total: float,
    credit_note_total: float,
    paid_total: float,
    payment_amount: float,
) -> None:
    if money(payment_amount) <= 0:
        raise ValueError("Supplier payment amount must be greater than zero")
    outstanding_total = money(max(0.0, invoice_total - credit_note_total - paid_total))
    if money(payment_amount) > outstanding_total:
        raise ValueError("Supplier payment exceeds outstanding amount")


def build_supplier_payables_report(
    *,
    branch_id: str,
    purchase_invoices: Iterable[Mapping[str, Any]],
    supplier_returns: Iterable[Mapping[str, Any]],
    supplier_payments: Iterable[Mapping[str, Any]],
    suppliers_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    credit_note_totals_by_invoice_id: dict[str, float] = {}
    for supplier_return in supplier_returns:
        purchase_invoice_id = str(supplier_return["purchase_invoice_id"])
        credit_note_totals_by_invoice_id[purchase_invoice_id] = money(
            credit_note_totals_by_invoice_id.get(purchase_invoice_id, 0.0) + float(supplier_return["grand_total"])
        )

    paid_totals_by_invoice_id: dict[str, float] = {}
    for supplier_payment in supplier_payments:
        purchase_invoice_id = str(supplier_payment["purchase_invoice_id"])
        paid_totals_by_invoice_id[purchase_invoice_id] = money(
            paid_totals_by_invoice_id.get(purchase_invoice_id, 0.0) + float(supplier_payment["amount"])
        )

    records: list[dict[str, Any]] = []
    invoiced_total = 0.0
    credit_note_total = 0.0
    paid_total = 0.0
    outstanding_total = 0.0

    for purchase_invoice in purchase_invoices:
        invoice_credit_note_total = credit_note_totals_by_invoice_id.get(str(purchase_invoice["id"]), 0.0)
        invoice_paid_total = paid_totals_by_invoice_id.get(str(purchase_invoice["id"]), 0.0)
        invoice_outstanding_total = money(
            max(0.0, float(purchase_invoice["grand_total"]) - invoice_credit_note_total - invoice_paid_total)
        )
        settlement_status = "UNPAID"
        if invoice_outstanding_total == 0:
            settlement_status = "SETTLED"
        elif invoice_credit_note_total > 0 or invoice_paid_total > 0:
            settlement_status = "PARTIALLY_SETTLED"

        supplier = suppliers_by_id.get(str(purchase_invoice["supplier_id"]))
        records.append(
            {
                "purchase_invoice_id": str(purchase_invoice["id"]),
                "purchase_invoice_number": str(purchase_invoice["invoice_number"]),
                "supplier_name": supplier["name"] if supplier else "Unknown supplier",
                "grand_total": money(float(purchase_invoice["grand_total"])),
                "credit_note_total": invoice_credit_note_total,
                "paid_total": invoice_paid_total,
                "outstanding_total": invoice_outstanding_total,
                "settlement_status": settlement_status,
            }
        )
        invoiced_total = money(invoiced_total + float(purchase_invoice["grand_total"]))
        credit_note_total = money(credit_note_total + invoice_credit_note_total)
        paid_total = money(paid_total + invoice_paid_total)
        outstanding_total = money(outstanding_total + invoice_outstanding_total)

    return {
        "branch_id": branch_id,
        "invoiced_total": invoiced_total,
        "credit_note_total": credit_note_total,
        "paid_total": paid_total,
        "outstanding_total": outstanding_total,
        "records": records,
    }
