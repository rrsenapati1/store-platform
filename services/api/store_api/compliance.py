from __future__ import annotations

from dataclasses import dataclass


def _state_code_from_gstin(gstin: str | None) -> str | None:
    normalized = (gstin or "").strip().upper()
    if len(normalized) < 2:
        return None
    return normalized[:2]


def calculate_invoice_taxes(
    *,
    seller_gstin: str | None,
    buyer_gstin: str | None,
    taxable_total: float,
    tax_rate_percent: float,
) -> dict[str, float]:
    tax_total = round(taxable_total * tax_rate_percent / 100, 2)
    same_state = _state_code_from_gstin(seller_gstin) and _state_code_from_gstin(seller_gstin) == _state_code_from_gstin(buyer_gstin)
    if same_state:
        half = round(tax_total / 2, 2)
        return {"cgst": half, "sgst": half, "igst": 0.0, "tax_total": tax_total}
    return {"cgst": 0.0, "sgst": 0.0, "igst": tax_total, "tax_total": tax_total}


def next_invoice_number(sequence: dict[tuple[str, str], int], *, branch_id: str, fiscal_year: str) -> str:
    key = (branch_id, fiscal_year)
    sequence[key] = sequence.get(key, 0) + 1
    return f"SINV-{fiscal_year}-{sequence[key]:06d}"


@dataclass(slots=True)
class GstExportJob:
    id: str
    invoice_id: str
    invoice_number: str
    seller_gstin: str
    buyer_gstin: str | None
    hsn_sac_code: str
    grand_total: float
    status: str


@dataclass(slots=True)
class IrnAttachment:
    invoice_id: str
    irn: str
    signed_qr_payload: str
    ack_no: str


def prepare_gst_export_job(
    *,
    invoice_id: str,
    invoice_number: str,
    seller_gstin: str,
    buyer_gstin: str | None,
    hsn_sac_code: str,
    grand_total: float,
) -> GstExportJob:
    return GstExportJob(
        id=f"gst-{invoice_id}",
        invoice_id=invoice_id,
        invoice_number=invoice_number,
        seller_gstin=seller_gstin,
        buyer_gstin=buyer_gstin,
        hsn_sac_code=hsn_sac_code,
        grand_total=grand_total,
        status="IRN_PENDING",
    )


def attach_irn_to_invoice(*, invoice_id: str, irn: str, signed_qr_payload: str, ack_no: str) -> IrnAttachment:
    return IrnAttachment(
        invoice_id=invoice_id,
        irn=irn,
        signed_qr_payload=signed_qr_payload,
        ack_no=ack_no,
    )
