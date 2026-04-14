import type { ThermalReceiptInput } from '@store/types';

function money(value: number): string {
  return value.toFixed(2);
}

export function buildThermalReceiptLines(receipt: ThermalReceiptInput): string[] {
  const lines = [
    'STORE TAX INVOICE',
    `Invoice: ${receipt.invoiceNumber}`,
    `Customer: ${receipt.customerName}`,
  ];

  if (receipt.gstin) {
    lines.push(`GSTIN: ${receipt.gstin}`);
  }

  for (const item of receipt.items) {
    lines.push(`${item.name} x${item.qty} @ ${money(item.unitPrice)} = ${money(item.lineTotal)}`);
  }

  lines.push(`Subtotal: ${money(receipt.totals.subtotal)}`);
  lines.push(`CGST: ${money(receipt.totals.cgst)}`);
  lines.push(`SGST: ${money(receipt.totals.sgst)}`);
  lines.push(`IGST: ${money(receipt.totals.igst)}`);
  lines.push(`Grand Total: ${money(receipt.totals.grandTotal)}`);
  lines.push(`IRN Status: ${receipt.irnStatus}`);
  return lines;
}
