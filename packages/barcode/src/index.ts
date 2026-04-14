import type { BarcodeLabelModel } from '@store/types';

export function normalizeScannedBarcode(value: string): string {
  return value.replace(/\s+/g, '').trim();
}

export function parseHidBuffer(buffer: string[]): string {
  const cutoff = buffer.indexOf('Enter');
  const relevant = cutoff >= 0 ? buffer.slice(0, cutoff) : buffer;
  return normalizeScannedBarcode(relevant.join(''));
}

export function allocateBarcode(input: { tenantCode: string; skuCode: string; existing?: string | null }): string {
  const existing = normalizeScannedBarcode(input.existing ?? '');
  if (existing) {
    return existing;
  }
  const token = `${input.tenantCode}${input.skuCode}`.toUpperCase().replace(/[^A-Z0-9]/g, '');
  return token.slice(0, 14);
}

export function buildBarcodeLabelModel(input: {
  skuCode: string;
  productName: string;
  barcode: string;
  sellingPrice: number;
}): BarcodeLabelModel {
  return {
    skuCode: input.skuCode,
    productName: input.productName,
    barcode: input.barcode,
    priceLabel: `Rs. ${input.sellingPrice.toFixed(2)}`,
  };
}
