from __future__ import annotations


def ensure_gst_export_allowed(
    *,
    invoice_kind: str,
    irn_status: str,
    seller_gstin: str | None,
    buyer_gstin: str | None,
) -> None:
    if not (seller_gstin or "").strip():
        raise ValueError("Branch GSTIN is required for GST export")
    if invoice_kind != "B2B":
        raise ValueError("GST export requires a B2B sale invoice")
    if not (buyer_gstin or "").strip():
        raise ValueError("Buyer GSTIN is required for GST export")
    if irn_status == "IRN_ATTACHED":
        raise ValueError("IRN is already attached for this sale invoice")


def ensure_irn_attachment_allowed(*, current_status: str, has_attachment: bool) -> None:
    if current_status == "IRN_ATTACHED" or has_attachment:
        raise ValueError("IRN is already attached for this export job")
    if current_status != "IRN_PENDING":
        raise ValueError("IRN can only be attached after GST export preparation is complete")


def build_hsn_sac_summary(hsn_sac_codes: list[str]) -> str:
    normalized_codes = sorted({code.strip().upper() for code in hsn_sac_codes if code and code.strip()})
    if not normalized_codes:
        raise ValueError("HSN or SAC codes are required for GST export")
    return ",".join(normalized_codes)
