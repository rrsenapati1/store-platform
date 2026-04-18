import type { ControlPlaneBranchCatalogItem } from '@store/types';

export type StoreSaleComplianceDraft = {
  salePrescriptionNumber: string;
  salePatientName: string;
  salePrescriberName: string;
  saleAgeVerified: boolean;
  saleAgeVerificationId: string;
};

export function isRxRequiredCatalogItem(item: ControlPlaneBranchCatalogItem | null | undefined) {
  return item?.compliance_profile === 'RX_REQUIRED';
}

export function isAgeRestrictedCatalogItem(item: ControlPlaneBranchCatalogItem | null | undefined) {
  return item?.compliance_profile === 'AGE_RESTRICTED';
}

export function resolveMinimumAge(item: ControlPlaneBranchCatalogItem | null | undefined) {
  const rawValue = item?.compliance_config?.minimum_age;
  const minimumAge = typeof rawValue === 'number' ? rawValue : Number(rawValue);
  if (!Number.isFinite(minimumAge) || minimumAge <= 0) {
    return null;
  }
  return minimumAge;
}

export function buildSaleComplianceCapture(
  selectedCatalogItem: ControlPlaneBranchCatalogItem | null,
  draft: StoreSaleComplianceDraft,
) {
  if (isRxRequiredCatalogItem(selectedCatalogItem)) {
    const prescriptionNumber = draft.salePrescriptionNumber.trim();
    const patientName = draft.salePatientName.trim();
    const prescriberName = draft.salePrescriberName.trim();
    if (!prescriptionNumber || !patientName || !prescriberName) {
      throw new Error('Prescription details are required for prescription-only products.');
    }
    return {
      prescription_number: prescriptionNumber,
      patient_name: patientName,
      prescriber_name: prescriberName,
    };
  }

  if (isAgeRestrictedCatalogItem(selectedCatalogItem)) {
    if (!draft.saleAgeVerified) {
      const minimumAge = resolveMinimumAge(selectedCatalogItem);
      throw new Error(
        minimumAge
          ? `Age verification is required for ${minimumAge}+ products.`
          : 'Age verification is required for age-restricted products.',
      );
    }
    const idReference = draft.saleAgeVerificationId.trim();
    return {
      age_verified: true,
      ...(idReference ? { id_reference: idReference } : {}),
    };
  }

  return null;
}

export function hasValidSaleComplianceInput(
  selectedCatalogItem: ControlPlaneBranchCatalogItem | null,
  draft: StoreSaleComplianceDraft,
) {
  if (isRxRequiredCatalogItem(selectedCatalogItem)) {
    return Boolean(
      draft.salePrescriptionNumber.trim()
      && draft.salePatientName.trim()
      && draft.salePrescriberName.trim(),
    );
  }

  if (isAgeRestrictedCatalogItem(selectedCatalogItem)) {
    return draft.saleAgeVerified;
  }

  return true;
}
