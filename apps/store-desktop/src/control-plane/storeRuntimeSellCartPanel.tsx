import { CommerceLineItem, SectionCard } from '@store/ui';
import { StoreBillingSection } from './StoreBillingSection';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function formatCurrency(value: number | null | undefined) {
  return Number(value ?? 0).toFixed(2);
}

function resolveLineDiscountAmount(line: {
  automatic_discount_amount: number;
  promotion_code_discount_amount: number;
  customer_voucher_discount_amount?: number | null;
}) {
  return line.automatic_discount_amount + line.promotion_code_discount_amount + Number(line.customer_voucher_discount_amount ?? 0);
}

function canRenderDetailedBilling(workspace: StoreRuntimeWorkspaceState) {
  return typeof workspace.createSalesInvoice === 'function'
    && typeof workspace.loadCustomerProfiles === 'function'
    && typeof workspace.setCustomerProfileSearchQuery === 'function'
    && Array.isArray(workspace.customerProfiles);
}

export function StoreRuntimeSellCartPanel({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const previewLines = workspace.checkoutPricePreview?.lines ?? [];
  const fallbackCatalogItem = workspace.branchCatalogItems[0] ?? null;

  return (
    <div style={{ display: 'grid', gap: '20px' }}>
      <SectionCard eyebrow="Sell" title="Current cart">
        <p style={{ marginTop: 0, color: '#4e5871' }}>
          Scanner-first cart posture with live commercial context.
        </p>
        {previewLines.length ? (
          <div>
            {previewLines.map((line) => (
              (() => {
                const discountAmount = resolveLineDiscountAmount(line);
                return (
                  <CommerceLineItem
                    key={`${line.product_id}-${line.quantity}`}
                    title={line.product_name}
                    meta={`MRP ${formatCurrency(line.mrp)} :: Selling ${formatCurrency(line.unit_selling_price)}`}
                    quantity={`Qty ${line.quantity}`}
                    amount={formatCurrency(line.line_total)}
                    secondary={
                      discountAmount ? (
                        <p style={{ margin: 0, fontSize: '12px', color: '#5a6477' }}>
                          {`Discount ${formatCurrency(discountAmount)} :: Tax ${formatCurrency(line.tax_amount)}`}
                        </p>
                      ) : undefined
                    }
                  />
                );
              })()
            ))}
          </div>
        ) : fallbackCatalogItem ? (
          <CommerceLineItem
            title={fallbackCatalogItem.product_name}
            meta={`${fallbackCatalogItem.sku_code ?? fallbackCatalogItem.barcode ?? 'No SKU'} :: ${fallbackCatalogItem.availability_status}`}
            amount={formatCurrency(fallbackCatalogItem.effective_selling_price)}
          >
            <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#5a6477' }}>
              Scan the barcode or confirm quantity to start the sale.
            </p>
          </CommerceLineItem>
        ) : (
          <p style={{ margin: 0, color: '#4e5871' }}>Scan a product to start the active cart.</p>
        )}
      </SectionCard>

      {canRenderDetailedBilling(workspace) ? <StoreBillingSection workspace={workspace} /> : null}
    </div>
  );
}
