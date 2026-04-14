import { describe, expect, test } from 'vitest';
import {
  allocateBarcode,
  buildBarcodeLabelModel,
  normalizeScannedBarcode,
  parseHidBuffer,
} from './index';

describe('barcode helpers', () => {
  test('normalizes scanned barcode payloads from HID and camera inputs', () => {
    expect(normalizeScannedBarcode('  8901234567890 \n')).toBe('8901234567890');
  });

  test('parses HID buffers until enter is received', () => {
    expect(parseHidBuffer(['8', '9', '0', '1', '2', '3', 'Enter'])).toBe('890123');
  });

  test('allocates a fallback barcode when no valid value is supplied', () => {
    expect(allocateBarcode({ tenantCode: 'TNT', skuCode: 'SKU-001', existing: '' })).toBe('TNTSKU001');
  });

  test('builds a print-friendly barcode label model', () => {
    expect(
      buildBarcodeLabelModel({
        skuCode: 'SKU-001',
        productName: 'Demo Product',
        barcode: '8901234567890',
        sellingPrice: 149.5,
      }),
    ).toEqual({
      skuCode: 'SKU-001',
      productName: 'Demo Product',
      barcode: '8901234567890',
      priceLabel: 'Rs. 149.50',
    });
  });
});
