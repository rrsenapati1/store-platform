import { describe, expect, test } from 'vitest';
import { buildThermalReceiptLines } from './index';

describe('thermal invoice rendering', () => {
  test('renders GST invoice totals and IRN pending posture for B2B invoices', () => {
    const lines = buildThermalReceiptLines({
      invoiceNumber: 'SINV-2526-000001',
      customerName: 'Acme Traders',
      gstin: '29ABCDE1234F1Z5',
      irnStatus: 'IRN_PENDING',
      items: [
        {
          name: 'Notebook',
          qty: 2,
          unitPrice: 100,
          lineTotal: 200,
        },
      ],
      totals: {
        subtotal: 200,
        cgst: 9,
        sgst: 9,
        igst: 0,
        grandTotal: 218,
      },
    });

    expect(lines).toContain('Invoice: SINV-2526-000001');
    expect(lines).toContain('Customer: Acme Traders');
    expect(lines).toContain('GSTIN: 29ABCDE1234F1Z5');
    expect(lines).toContain('CGST: 9.00');
    expect(lines).toContain('SGST: 9.00');
    expect(lines).toContain('IRN Status: IRN_PENDING');
  });
});
