from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import Any

from .purchase_policy import money, normalize_gstin


def _state_code(gstin: str | None) -> str:
    normalized = normalize_gstin(gstin)
    if not normalized or len(normalized) < 2:
        return ""
    return normalized[:2]


def _require_text(value: str, *, label: str) -> str:
    normalized = (value or "").strip()
    if not normalized:
        raise ValueError(f"{label} is required for IRP submission")
    return normalized


def _format_doc_date(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def build_irp_invoice_payload(
    *,
    sale_bundle,
    branch,
    products_by_id: Mapping[str, Any],
    seller_profile,
    buyer_profile,
) -> dict[str, object]:
    seller_gstin = _require_text(branch.gstin or "", label="Seller GSTIN")
    buyer_gstin = _require_text(sale_bundle.sale.customer_gstin or "", label="Buyer GSTIN")
    seller_state_code = _require_text(seller_profile.state_code or _state_code(seller_gstin), label="Seller state code")
    buyer_state_code = _require_text(buyer_profile.state_code or _state_code(buyer_gstin), label="Buyer state code")
    is_inter_state = seller_state_code != buyer_state_code

    item_list: list[dict[str, object]] = []
    for index, line in enumerate(sale_bundle.lines, start=1):
        product = products_by_id.get(line.product_id)
        if product is None:
            raise ValueError("Catalog product not found for GST export line item")
        if is_inter_state:
            igst_amount = money(line.tax_total)
            cgst_amount = 0.0
            sgst_amount = 0.0
        else:
            cgst_amount = money(line.tax_total / 2)
            sgst_amount = money(line.tax_total - cgst_amount)
            igst_amount = 0.0
        item_list.append(
            {
                "SlNo": str(index),
                "PrdDesc": _require_text(str(product.name), label="Product name"),
                "IsServc": "N",
                "HsnCd": _require_text(str(product.hsn_sac_code), label="HSN or SAC code"),
                "Qty": money(line.quantity),
                "Unit": "NOS",
                "UnitPrice": money(line.unit_price),
                "TotAmt": money(line.line_subtotal),
                "AssAmt": money(line.line_subtotal),
                "GstRt": money(line.gst_rate),
                "IgstAmt": igst_amount,
                "CgstAmt": cgst_amount,
                "SgstAmt": sgst_amount,
                "TotItemVal": money(line.line_total),
            }
        )

    return {
        "Version": "1.1",
        "TranDtls": {"TaxSch": "GST", "SupTyp": "B2B"},
        "DocDtls": {
            "Typ": "INV",
            "No": sale_bundle.invoice.invoice_number,
            "Dt": _format_doc_date(sale_bundle.invoice.issued_on),
        },
        "SellerDtls": {
            "Gstin": seller_gstin,
            "LglNm": _require_text(seller_profile.legal_name or branch.name, label="Seller legal name"),
            "TrdNm": _require_text(seller_profile.trade_name or seller_profile.legal_name or branch.name, label="Seller trade name"),
            "Addr1": _require_text(seller_profile.address_line1, label="Seller address line 1"),
            "Addr2": seller_profile.address_line2 or "",
            "Loc": _require_text(seller_profile.location, label="Seller location"),
            "Pin": int(_require_text(seller_profile.pincode, label="Seller pincode")),
            "Stcd": seller_state_code,
        },
        "BuyerDtls": {
            "Gstin": buyer_gstin,
            "LglNm": _require_text(buyer_profile.legal_name or sale_bundle.sale.customer_name, label="Buyer legal name"),
            "TrdNm": _require_text(buyer_profile.trade_name or buyer_profile.legal_name or sale_bundle.sale.customer_name, label="Buyer trade name"),
            "Pos": buyer_state_code,
            "Addr1": _require_text(buyer_profile.address_line1, label="Buyer address line 1"),
            "Addr2": buyer_profile.address_line2 or "",
            "Loc": _require_text(buyer_profile.location, label="Buyer location"),
            "Pin": int(_require_text(buyer_profile.pincode, label="Buyer pincode")),
            "Stcd": buyer_state_code,
        },
        "ItemList": item_list,
        "ValDtls": {
            "AssVal": money(sale_bundle.invoice.subtotal),
            "CgstVal": money(sale_bundle.invoice.cgst_total),
            "SgstVal": money(sale_bundle.invoice.sgst_total),
            "IgstVal": money(sale_bundle.invoice.igst_total),
            "TotInvVal": money(sale_bundle.invoice.grand_total),
        },
    }
