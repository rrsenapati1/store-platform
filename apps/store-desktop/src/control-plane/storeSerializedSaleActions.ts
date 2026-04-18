import type { ControlPlaneBranchCatalogItem } from '@store/types';
import {
  buildSaleComplianceCapture,
  type StoreSaleComplianceDraft,
} from './storeSaleComplianceActions';

export function isSerializedCatalogItem(item: ControlPlaneBranchCatalogItem | null | undefined) {
  return item?.tracking_mode === 'SERIALIZED';
}

export function parseSaleSerialNumbers(raw: string): string[] {
  return raw
    .split(/\r?\n|,/)
    .map((value) => value.trim())
    .filter(Boolean);
}

export function validateSerializedSaleInput(
  selectedCatalogItem: ControlPlaneBranchCatalogItem | null,
  saleQuantity: string,
  rawSerialNumbers: string,
) {
  const quantity = Number(saleQuantity);
  if (!Number.isFinite(quantity) || quantity <= 0) {
    throw new Error('Sale quantity must be a positive number.');
  }

  const serialNumbers = parseSaleSerialNumbers(rawSerialNumbers);
  if (isSerializedCatalogItem(selectedCatalogItem) && serialNumbers.length !== quantity) {
    throw new Error('Serialized sales require one serial / IMEI number per unit.');
  }

  return {
    quantity,
    serialNumbers,
  };
}

export function buildSerializedSaleLineInput(
  selectedCatalogItem: ControlPlaneBranchCatalogItem | null,
  saleQuantity: string,
  rawSerialNumbers: string,
  complianceDraft: StoreSaleComplianceDraft,
) {
  if (!selectedCatalogItem) {
    throw new Error('Select a billable catalog item before billing.');
  }

  const { quantity, serialNumbers } = validateSerializedSaleInput(
    selectedCatalogItem,
    saleQuantity,
    rawSerialNumbers,
  );
  const complianceCapture = buildSaleComplianceCapture(selectedCatalogItem, complianceDraft);

  return {
    product_id: selectedCatalogItem.product_id,
    quantity,
    ...(serialNumbers.length ? { serial_numbers: serialNumbers } : {}),
    ...(complianceCapture ? { compliance_capture: complianceCapture } : {}),
  };
}
