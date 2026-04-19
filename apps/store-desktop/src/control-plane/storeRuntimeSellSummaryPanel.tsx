import { CommerceSummaryRow, CommerceTotalsBlock, SectionCard } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function formatCurrency(value: number | null | undefined) {
  return Number(value ?? 0).toFixed(2);
}

export function StoreRuntimeSellSummaryPanel({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const preview = workspace.checkoutPricePreview;
  const summary = preview?.summary;
  const customerName = workspace.selectedCustomerProfile?.full_name ?? 'Walk-in customer';
  const customerTier = workspace.selectedCustomerProfile?.default_price_tier_display_name ?? 'Standard pricing';

  return (
    <SectionCard eyebrow="Commercial posture" title="Customer and totals">
      <p style={{ marginTop: 0, color: '#4e5871' }}>
        Keep the commercial truth visible before payment.
      </p>
      <div style={{ display: 'grid', gap: '18px' }}>
        <div>
          <p style={{ margin: 0, fontSize: '12px', letterSpacing: '0.08em', textTransform: 'uppercase', color: '#6b7487' }}>Customer</p>
          <h3 style={{ margin: '6px 0 4px', fontSize: '20px', lineHeight: 1.25 }}>{customerName}</h3>
          <p style={{ margin: 0, color: '#4e5871' }}>{customerTier}</p>
        </div>

        <CommerceTotalsBlock title="Benefits">
          <CommerceSummaryRow
            label="Store credit"
            value={workspace.selectedCustomerStoreCredit ? formatCurrency(workspace.selectedCustomerStoreCredit.available_balance) : '0.00'}
          />
          <CommerceSummaryRow
            label="Loyalty"
            value={workspace.selectedCustomerLoyalty ? `${workspace.selectedCustomerLoyalty.available_points} pts` : '0 pts'}
          />
          <CommerceSummaryRow
            label="Voucher"
            value={workspace.selectedCustomerVoucher ? workspace.selectedCustomerVoucher.voucher_code : 'None'}
          />
        </CommerceTotalsBlock>

        <CommerceTotalsBlock title="Invoice">
          <CommerceSummaryRow label="MRP total" value={formatCurrency(summary?.mrp_total)} />
          <CommerceSummaryRow label="Selling subtotal" value={formatCurrency(summary?.selling_price_subtotal)} />
          <CommerceSummaryRow label="Discount" value={formatCurrency(summary?.total_discount)} />
          <CommerceSummaryRow label="Tax" value={formatCurrency(summary?.tax_total)} />
          <CommerceSummaryRow label="Invoice total" value={formatCurrency(summary?.invoice_total)} emphasis />
        </CommerceTotalsBlock>
      </div>
    </SectionCard>
  );
}
