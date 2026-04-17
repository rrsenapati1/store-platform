import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { OwnerWorkspaceState } from './useOwnerWorkspace';

export function OwnerPriceTierSection({ workspace }: { workspace: OwnerWorkspaceState }) {
  const firstProduct = workspace.catalogProducts[0];
  const firstPriceTier = workspace.priceTiers[0];

  return (
    <>
      <SectionCard eyebrow="Commercial pricing foundation" title="Price tiers">
        <FormField id="price-tier-code" label="Price tier code" value={workspace.priceTierCode} onChange={workspace.setPriceTierCode} placeholder="VIP" />
        <FormField
          id="price-tier-display-name"
          label="Price tier display name"
          value={workspace.priceTierDisplayName}
          onChange={workspace.setPriceTierDisplayName}
          placeholder="VIP Price"
        />
        <FormField
          id="price-tier-status"
          label="Price tier status"
          value={workspace.priceTierStatus}
          onChange={workspace.setPriceTierStatus}
          placeholder="ACTIVE or DISABLED"
        />
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <ActionButton
            onClick={() => void workspace.createPriceTier()}
            disabled={workspace.isBusy || !workspace.actor || !workspace.tenantId || !workspace.branchId || !workspace.priceTierCode || !workspace.priceTierDisplayName}
          >
            Create price tier
          </ActionButton>
          <ActionButton onClick={() => void workspace.loadPriceTiers()} disabled={workspace.isBusy || !workspace.actor || !workspace.tenantId || !workspace.branchId}>
            Load price tiers
          </ActionButton>
        </div>

        {workspace.latestPriceTier ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest price tier</h3>
            <DetailList
              items={[
                { label: 'Code', value: workspace.latestPriceTier.code },
                { label: 'Display name', value: workspace.latestPriceTier.display_name },
                { label: 'Status', value: <StatusBadge label={workspace.latestPriceTier.status} tone={workspace.latestPriceTier.status === 'ACTIVE' ? 'success' : 'warning'} /> },
              ]}
            />
          </div>
        ) : null}

        <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.priceTiers.length ? (
            workspace.priceTiers.map((tier) => (
              <li key={tier.id}>
                {tier.code} :: {tier.display_name} :: {tier.status}
              </li>
            ))
          ) : (
            <li>No price tiers loaded yet.</li>
          )}
        </ul>
      </SectionCard>

      <SectionCard eyebrow="Branch tier pricing" title="Tier-specific branch price">
        <FormField
          id="branch-price-tier-selling-price"
          label="Tier selling price"
          value={workspace.branchPriceTierSellingPrice}
          onChange={workspace.setBranchPriceTierSellingPrice}
          placeholder="84"
        />
        <ActionButton
          onClick={() => void workspace.upsertFirstBranchPriceTierPrice()}
          disabled={
            workspace.isBusy ||
            !workspace.actor ||
            !workspace.branchId ||
            !firstProduct ||
            !firstPriceTier ||
            !workspace.branchPriceTierSellingPrice
          }
        >
          Set first tier price for first product
        </ActionButton>

        {workspace.latestBranchPriceTierPrice ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest branch tier price</h3>
            <DetailList
              items={[
                { label: 'Product', value: workspace.latestBranchPriceTierPrice.product_name },
                { label: 'Tier', value: workspace.latestBranchPriceTierPrice.price_tier_display_name },
                { label: 'Base selling price', value: String(workspace.latestBranchPriceTierPrice.effective_base_selling_price) },
                { label: 'Tier price', value: String(workspace.latestBranchPriceTierPrice.selling_price) },
              ]}
            />
          </div>
        ) : null}

        <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.branchPriceTierPrices.length ? (
            workspace.branchPriceTierPrices.map((record) => (
              <li key={record.id}>
                {record.product_name} :: {record.price_tier_code} :: {record.selling_price}
              </li>
            ))
          ) : (
            <li>No branch price-tier prices loaded yet.</li>
          )}
        </ul>
      </SectionCard>
    </>
  );
}
