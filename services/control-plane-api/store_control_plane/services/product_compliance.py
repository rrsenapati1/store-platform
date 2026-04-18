from __future__ import annotations

from fastapi import HTTPException, status


SUPPORTED_COMPLIANCE_PROFILES = {"NONE", "RX_REQUIRED", "AGE_RESTRICTED"}


def normalize_product_compliance(
    *,
    compliance_profile: str | None,
    compliance_config: dict[str, object] | None,
) -> tuple[str, dict[str, object]]:
    resolved_profile = str(compliance_profile or "NONE").strip().upper()
    if resolved_profile not in SUPPORTED_COMPLIANCE_PROFILES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported compliance profile")

    raw_config = dict(compliance_config or {})
    if resolved_profile == "NONE":
        return "NONE", {}
    if resolved_profile == "RX_REQUIRED":
        return "RX_REQUIRED", {}

    minimum_age = raw_config.get("minimum_age")
    if minimum_age is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum age is required for age-restricted products",
        )
    try:
        resolved_minimum_age = int(minimum_age)
    except (TypeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum age must be a whole number",
        ) from error
    if resolved_minimum_age <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum age must be greater than zero",
        )
    return "AGE_RESTRICTED", {"minimum_age": resolved_minimum_age}


def normalize_sale_line_compliance(
    *,
    compliance_profile: str | None,
    compliance_config: dict[str, object] | None,
    compliance_capture: dict[str, object] | None,
) -> tuple[str, dict[str, object]]:
    resolved_profile, resolved_config = normalize_product_compliance(
        compliance_profile=compliance_profile,
        compliance_config=compliance_config,
    )
    raw_capture = dict(compliance_capture or {})

    if resolved_profile == "NONE":
        return "NONE", {}

    if resolved_profile == "RX_REQUIRED":
        prescription_number = str(raw_capture.get("prescription_number") or "").strip()
        patient_name = str(raw_capture.get("patient_name") or "").strip()
        prescriber_name = str(raw_capture.get("prescriber_name") or "").strip()
        if not prescription_number or not patient_name or not prescriber_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prescription details are required for prescription-only products",
            )
        return "RX_REQUIRED", {
            "prescription_number": prescription_number,
            "patient_name": patient_name,
            "prescriber_name": prescriber_name,
        }

    age_verified = raw_capture.get("age_verified") is True
    if not age_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Age verification is required for age-restricted products",
        )
    normalized_capture: dict[str, object] = {
        "age_verified": True,
        "minimum_age": int(resolved_config["minimum_age"]),
    }
    id_reference = str(raw_capture.get("id_reference") or "").strip()
    if id_reference:
        normalized_capture["id_reference"] = id_reference
    return "AGE_RESTRICTED", normalized_capture
