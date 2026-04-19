import { useEffect, useMemo, useState } from 'react';
import {
  DetailList,
  FormField,
  OwnerCommandHeader,
  OwnerCommandShell,
  OwnerExceptionBoard,
  OwnerNavRail,
  OwnerPanel,
  OwnerSignalRow,
  SectionCard,
  StatusBadge,
  StoreThemeModeToggle,
} from '@store/ui';
import { OwnerBatchExpirySection } from './OwnerBatchExpirySection';
import { OwnerAttendanceSection } from './OwnerAttendanceSection';
import { OwnerBarcodeSection } from './OwnerBarcodeSection';
import { OwnerBarcodePrintRuntimeSection } from './OwnerBarcodePrintRuntimeSection';
import { OwnerBillingLifecycleSection } from './OwnerBillingLifecycleSection';
import { OwnerBranchPerformanceSection } from './OwnerBranchPerformanceSection';
import { OwnerCashierSessionSection } from './OwnerCashierSessionSection';
import { OwnerComplianceSection } from './OwnerComplianceSection';
import { OwnerCustomerInsightsSection } from './OwnerCustomerInsightsSection';
import { OwnerDeviceClaimSection } from './OwnerDeviceClaimSection';
import { OwnerGiftCardSection } from './OwnerGiftCardSection';
import { OwnerRuntimePolicySection } from './OwnerRuntimePolicySection';
import { OwnerShiftSessionSection } from './OwnerShiftSessionSection';
import { OwnerSupplierReportingSection } from './OwnerSupplierReportingSection';
import { OwnerSyncRuntimeSection } from './OwnerSyncRuntimeSection';
import { OwnerInventoryControlSection } from './OwnerInventoryControlSection';
import { OwnerProcurementFinanceSection } from './OwnerProcurementFinanceSection';
import { OwnerProcurementSection } from './OwnerProcurementSection';
import { OwnerPriceTierSection } from './OwnerPriceTierSection';
import { OwnerPromotionCampaignSection } from './OwnerPromotionCampaignSection';
import { OwnerReplenishmentSection } from './OwnerReplenishmentSection';
import { OwnerRestockSection } from './OwnerRestockSection';
import { OwnerReturnApprovalsSection } from './OwnerReturnApprovalsSection';
import { OwnerReceivingSection } from './OwnerReceivingSection';
import { OwnerWorkforceAuditSection } from './OwnerWorkforceAuditSection';
import type { OwnerWorkspaceState } from './useOwnerWorkspace';

type OwnerConsoleScreenId = 'overview' | 'operations' | 'commercial' | 'catalog' | 'workforce' | 'settings';

const OWNER_NAV_ITEMS: Array<{ id: OwnerConsoleScreenId; label: string }> = [
  { id: 'overview', label: 'Overview' },
  { id: 'operations', label: 'Operations' },
  { id: 'commercial', label: 'Commercial' },
  { id: 'catalog', label: 'Catalog' },
  { id: 'workforce', label: 'Workforce' },
  { id: 'settings', label: 'Settings' },
];

const SCREEN_COPY: Record<OwnerConsoleScreenId, { title: string; subtitle: string }> = {
  overview: {
    title: 'Tenant overview',
    subtitle: 'Live posture, exceptions, and branch drill-down for day-to-day owner supervision.',
  },
  operations: {
    title: 'Operations',
    subtitle: 'Procurement, receiving, stock control, expiry, replenishment, and branch operating exceptions.',
  },
  commercial: {
    title: 'Commercial',
    subtitle: 'Pricing, promotions, lifecycle posture, customer levers, and revenue-facing controls.',
  },
  catalog: {
    title: 'Catalog',
    subtitle: 'Product authority, barcode operations, branch catalog posture, and label-print runtime.',
  },
  workforce: {
    title: 'Workforce',
    subtitle: 'People, devices, attendance, shifts, cashier governance, and runtime policy.',
  },
  settings: {
    title: 'Settings',
    subtitle: 'Tenant state, branch setup, onboarding controls, and audit visibility.',
  },
};

function buildOverviewSignals(workspace: OwnerWorkspaceState, branchScope: string) {
  const scopedBranchCount = branchScope === 'all' ? workspace.branches.length : Number(Boolean(workspace.branchId));
  return [
    {
      label: 'Branches in scope',
      value: String(scopedBranchCount),
      tone: scopedBranchCount > 0 ? 'success' : 'warning',
    },
    {
      label: 'Catalog products',
      value: String(workspace.catalogProducts.length),
      tone: workspace.catalogProducts.length > 0 ? 'success' : 'warning',
    },
    {
      label: 'Team profiles',
      value: String(workspace.staffProfiles.length),
      tone: workspace.staffProfiles.length > 0 ? 'success' : 'warning',
    },
    {
      label: 'Registered devices',
      value: String(workspace.devices.length),
      tone: workspace.devices.length > 0 ? 'success' : 'warning',
    },
    {
      label: 'Suppliers',
      value: String(workspace.suppliers.length),
      tone: workspace.suppliers.length > 0 ? 'success' : 'warning',
    },
    {
      label: 'Audit events',
      value: String(workspace.auditEvents.length),
    },
  ] as const;
}

function OwnerOverviewScreen(props: {
  workspace: OwnerWorkspaceState;
  branchScope: string;
  onSelectScreen: (screenId: OwnerConsoleScreenId) => void;
}) {
  const signals = buildOverviewSignals(props.workspace, props.branchScope);
  const selectedBranch = props.workspace.branches.find((branch) => branch.branch_id === props.workspace.branchId);
  const exceptionItems = [
    props.workspace.branches.length === 0
      ? {
          id: 'setup-branch',
          title: 'Create your first branch',
          detail: 'The owner console is live, but no branch runtime is provisioned yet.',
          ctaLabel: 'Open settings',
          onSelect: () => props.onSelectScreen('settings'),
        }
      : null,
    props.workspace.catalogProducts.length === 0
      ? {
          id: 'seed-catalog',
          title: 'Seed the product catalog',
          detail: 'No central catalog products exist yet, so branch pricing and barcode flows cannot start.',
          ctaLabel: 'Open catalog',
          onSelect: () => props.onSelectScreen('catalog'),
        }
      : null,
    props.workspace.branches.length > 0 && props.workspace.branchCatalogItems.length === 0
      ? {
          id: 'assign-catalog',
          title: 'Assign products to a branch',
          detail: 'Central products exist, but no branch catalog assignment has been created for the active branch.',
          ctaLabel: 'Review catalog',
          onSelect: () => props.onSelectScreen('catalog'),
        }
      : null,
    props.workspace.staffProfiles.length === 0
      ? {
          id: 'seed-staff',
          title: 'Bootstrap the workforce',
          detail: 'No staff profiles are registered yet, so attendance, cashier, and device flows are blocked.',
          ctaLabel: 'Open workforce',
          onSelect: () => props.onSelectScreen('workforce'),
        }
      : null,
    props.workspace.branches.length > 0 && props.workspace.devices.length === 0
      ? {
          id: 'register-device',
          title: 'Register branch hardware',
          detail: 'Branch devices have not been claimed yet, so runtime rollout is still incomplete.',
          ctaLabel: 'Open workforce',
          onSelect: () => props.onSelectScreen('workforce'),
        }
      : null,
    props.workspace.purchaseOrders.length > 0 && props.workspace.goodsReceipts.length === 0
      ? {
          id: 'receive-stock',
          title: 'Purchase orders need receiving',
          detail: 'Open receiving to capture goods receipts and unblock inventory intake.',
          ctaLabel: 'Open operations',
          onSelect: () => props.onSelectScreen('operations'),
        }
      : null,
  ].filter((item): item is NonNullable<typeof item> => item !== null);

  return (
    <>
      {props.workspace.errorMessage ? (
        <OwnerPanel title="Workspace alert" subtitle="The latest owner action returned an error.">
          <p style={{ margin: 0, color: 'var(--store-danger, #9d2b19)', lineHeight: 1.6 }}>{props.workspace.errorMessage}</p>
        </OwnerPanel>
      ) : null}

      <OwnerSignalRow items={signals.map((item) => ({ ...item }))} />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        <OwnerPanel
          title="Attention now"
          subtitle="Critical owner actions are elevated here before they turn into runtime pain."
        >
          <OwnerExceptionBoard items={exceptionItems} emptyState="No critical owner setup or operations exceptions are active." />
        </OwnerPanel>
        <OwnerPanel
          title="Branch scope"
          subtitle={
            props.branchScope === 'all'
              ? 'Cross-branch posture is active. Choose a branch when you want branch-specific drill-down cards.'
              : 'Branch-specific overview detail and downstream operational screens target the selected branch.'
          }
        >
          {props.branchScope === 'all' ? (
            <DetailList
              items={[
                { label: 'Actor', value: props.workspace.actor?.full_name ?? 'Unavailable' },
                { label: 'Overview scope', value: 'All branches' },
                { label: 'Known branches', value: String(props.workspace.branches.length) },
                { label: 'Onboarding', value: props.workspace.tenant?.onboarding_status ?? 'Pending' },
                { label: 'Audit events', value: String(props.workspace.auditEvents.length) },
              ]}
            />
          ) : (
            <DetailList
              items={[
                { label: 'Actor', value: props.workspace.actor?.full_name ?? 'Unavailable' },
                { label: 'Branch', value: (selectedBranch?.name ?? props.workspace.branchId) || 'Unavailable' },
                { label: 'Code', value: selectedBranch?.code ?? 'Unavailable' },
                { label: 'Runtime devices', value: String(props.workspace.devices.length) },
                { label: 'Catalog assignments', value: String(props.workspace.branchCatalogItems.length) },
              ]}
            />
          )}
        </OwnerPanel>
      </div>

      <OwnerBranchPerformanceSection
        accessToken={props.workspace.accessToken}
        tenantId={props.workspace.tenantId}
        branches={props.workspace.branches}
      />

      <OwnerPanel title="Recent audit feed" subtitle="The newest tenant-side onboarding and control-plane actions remain visible from the default landing surface.">
        {props.workspace.auditEvents.length === 0 ? (
          <p style={{ margin: 0, color: 'var(--store-text-muted, #5a6477)', lineHeight: 1.6 }}>No audit events have been captured yet.</p>
        ) : (
          <ul style={{ margin: 0, paddingLeft: '20px', color: 'var(--store-text-muted, #5a6477)', lineHeight: 1.7 }}>
            {props.workspace.auditEvents.slice(0, 6).map((event) => (
              <li key={event.id}>{event.action}</li>
            ))}
          </ul>
        )}
      </OwnerPanel>

      {props.branchScope === 'all' ? (
        <OwnerPanel
          title="Branch-specific detail"
          subtitle="Pick a branch in the command header to unlock sync, customer, and supplier drill-down cards."
        >
          <p style={{ margin: 0, color: 'var(--store-text-muted, #5a6477)', lineHeight: 1.6 }}>
            Overview stays cross-branch by default. Once you choose a branch, the lower detail cards focus on that branch and the
            operational tabs inherit the same concrete target.
          </p>
        </OwnerPanel>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
          <OwnerSyncRuntimeSection
            accessToken={props.workspace.accessToken}
            tenantId={props.workspace.tenantId}
            branchId={props.workspace.branchId}
          />
          <OwnerCustomerInsightsSection
            accessToken={props.workspace.accessToken}
            tenantId={props.workspace.tenantId}
            branchId={props.workspace.branchId}
          />
          <OwnerSupplierReportingSection
            accessToken={props.workspace.accessToken}
            tenantId={props.workspace.tenantId}
            branchId={props.workspace.branchId}
          />
        </div>
      )}
    </>
  );
}

function OwnerSettingsScreen(props: { workspace: OwnerWorkspaceState }) {
  return (
    <>
      <OwnerPanel title="Tenant posture" subtitle="Commercial readiness and the current onboarding state for the tenant root.">
        {props.workspace.tenant ? (
          <DetailList
            items={[
              { label: 'Tenant', value: props.workspace.tenant.name },
              { label: 'Slug', value: props.workspace.tenant.slug },
              {
                label: 'Status',
                value: (
                  <StatusBadge
                    label={props.workspace.tenant.onboarding_status}
                    tone={props.workspace.tenant.onboarding_status === 'BRANCH_READY' ? 'success' : 'warning'}
                  />
                ),
              },
            ]}
          />
        ) : (
          <p style={{ margin: 0, color: 'var(--store-text-muted, #5a6477)' }}>Session bootstrap is still loading tenant posture.</p>
        )}
      </OwnerPanel>

      <SectionCard eyebrow="First branch setup" title="Branch creation">
        <FormField id="branch-name" label="Branch name" value={props.workspace.branchName} onChange={props.workspace.setBranchName} />
        <FormField id="branch-code" label="Branch code" value={props.workspace.branchCode} onChange={props.workspace.setBranchCode} />
        <FormField id="branch-gstin" label="Branch GSTIN" value={props.workspace.branchGstin} onChange={props.workspace.setBranchGstin} />
        <button
          type="button"
          onClick={() => void props.workspace.createFirstBranch()}
          disabled={props.workspace.isBusy || !props.workspace.actor || !props.workspace.branchName || !props.workspace.branchCode}
          style={{ display: 'none' }}
          aria-hidden="true"
        />
        <div>
          <button
            type="button"
            onClick={() => void props.workspace.createFirstBranch()}
            disabled={props.workspace.isBusy || !props.workspace.actor || !props.workspace.branchName || !props.workspace.branchCode}
            style={{
              border: 0,
              borderRadius: 'var(--store-radius-pill, 999px)',
              padding: '11px 18px',
              fontSize: '14px',
              fontWeight: 700,
              background: props.workspace.isBusy || !props.workspace.actor || !props.workspace.branchName || !props.workspace.branchCode
                ? 'var(--store-border-strong, #c5cad7)'
                : 'var(--store-accent, #172033)',
              color: '#ffffff',
              cursor: props.workspace.isBusy || !props.workspace.actor || !props.workspace.branchName || !props.workspace.branchCode
                ? 'not-allowed'
                : 'pointer',
            }}
          >
            Create first branch
          </button>
        </div>
        <ul style={{ marginBottom: 0, marginTop: '16px', color: 'var(--store-text-muted, #5a6477)', lineHeight: 1.7 }}>
          {props.workspace.branches.map((branch) => (
            <li key={branch.branch_id}>{branch.name}</li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard eyebrow="Audit foundation" title="Onboarding audit feed">
        <ul style={{ marginBottom: 0, color: 'var(--store-text-muted, #5a6477)', lineHeight: 1.7 }}>
          {props.workspace.auditEvents.map((event) => (
            <li key={event.id}>{event.action}</li>
          ))}
        </ul>
      </SectionCard>
    </>
  );
}

function OwnerCatalogScreen(props: { workspace: OwnerWorkspaceState }) {
  const { workspace } = props;

  return (
    <>
      <SectionCard eyebrow="Central catalog foundation" title="Catalog product setup">
        <FormField id="product-name" label="Product name" value={workspace.productName} onChange={workspace.setProductName} />
        <FormField id="product-sku-code" label="SKU code" value={workspace.productSkuCode} onChange={workspace.setProductSkuCode} />
        <FormField id="product-barcode" label="Barcode" value={workspace.productBarcode} onChange={workspace.setProductBarcode} />
        <FormField id="product-hsn-sac-code" label="HSN or SAC code" value={workspace.productHsnSacCode} onChange={workspace.setProductHsnSacCode} />
        <FormField id="product-gst-rate" label="GST rate" value={workspace.productGstRate} onChange={workspace.setProductGstRate} />
        <FormField id="product-mrp" label="MRP" value={workspace.productMrp} onChange={workspace.setProductMrp} />
        <FormField id="product-category-code" label="Category code" value={workspace.productCategoryCode} onChange={workspace.setProductCategoryCode} />
        <FormField id="product-tracking-mode" label="Tracking mode" value={workspace.productTrackingMode} onChange={workspace.setProductTrackingMode} />
        <FormField
          id="product-compliance-profile"
          label="Compliance profile"
          value={workspace.productComplianceProfile}
          onChange={workspace.setProductComplianceProfile}
        />
        {workspace.productComplianceProfile === 'AGE_RESTRICTED' ? (
          <FormField id="product-minimum-age" label="Minimum age" value={workspace.productMinimumAge} onChange={workspace.setProductMinimumAge} />
        ) : null}
        <FormField id="product-selling-price" label="Selling price" value={workspace.productSellingPrice} onChange={workspace.setProductSellingPrice} />
        <button
          type="button"
          onClick={() => void workspace.createCatalogProduct()}
          disabled={
            workspace.isBusy
            || !workspace.actor
            || !workspace.productName
            || !workspace.productSkuCode
            || !workspace.productBarcode
            || !workspace.productHsnSacCode
            || !workspace.productMrp
            || (workspace.productComplianceProfile === 'AGE_RESTRICTED' && !workspace.productMinimumAge)
            || !workspace.productSellingPrice
          }
          style={{
            border: 0,
            borderRadius: 'var(--store-radius-pill, 999px)',
            padding: '11px 18px',
            fontSize: '14px',
            fontWeight: 700,
            background: workspace.isBusy
              || !workspace.actor
              || !workspace.productName
              || !workspace.productSkuCode
              || !workspace.productBarcode
              || !workspace.productHsnSacCode
              || !workspace.productMrp
              || (workspace.productComplianceProfile === 'AGE_RESTRICTED' && !workspace.productMinimumAge)
              || !workspace.productSellingPrice
              ? 'var(--store-border-strong, #c5cad7)'
              : 'var(--store-accent, #172033)',
            color: '#ffffff',
            cursor: workspace.isBusy ? 'not-allowed' : 'pointer',
          }}
        >
          Create catalog product
        </button>

        {workspace.latestCatalogProduct ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest catalog product</h3>
            <DetailList
              items={[
                { label: 'Name', value: workspace.latestCatalogProduct.name },
                { label: 'SKU', value: workspace.latestCatalogProduct.sku_code },
                { label: 'MRP', value: String(workspace.latestCatalogProduct.mrp) },
                { label: 'Category', value: workspace.latestCatalogProduct.category_code ?? 'Unspecified' },
                { label: 'Tracking mode', value: workspace.latestCatalogProduct.tracking_mode },
                { label: 'Compliance profile', value: workspace.latestCatalogProduct.compliance_profile ?? 'NONE' },
                {
                  label: 'Minimum age',
                  value: String((workspace.latestCatalogProduct.compliance_config?.minimum_age as number | undefined) ?? 'Not required'),
                },
                { label: 'Status', value: <StatusBadge label={workspace.latestCatalogProduct.status} tone="success" /> },
              ]}
            />
          </div>
        ) : null}

        <ul style={{ marginBottom: 0, marginTop: '16px', color: 'var(--store-text-muted, #5a6477)', lineHeight: 1.7 }}>
          {workspace.catalogProducts.map((product) => (
            <li key={product.product_id}>
              {product.name} ({product.sku_code}) :: MRP {product.mrp} :: {product.category_code ?? 'NO_CATEGORY'} :: {product.tracking_mode}
            </li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard eyebrow="Branch catalog foundation" title="Branch catalog assignment">
        <FormField
          id="branch-catalog-price-override"
          label="Branch selling price override"
          value={workspace.branchCatalogPriceOverride}
          onChange={workspace.setBranchCatalogPriceOverride}
          placeholder="Optional override for the first catalog product"
        />
        <button
          type="button"
          onClick={() => void workspace.assignFirstProductToBranch()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.branchId || workspace.catalogProducts.length === 0}
          style={{
            border: 0,
            borderRadius: 'var(--store-radius-pill, 999px)',
            padding: '11px 18px',
            fontSize: '14px',
            fontWeight: 700,
            background: workspace.isBusy || !workspace.actor || !workspace.branchId || workspace.catalogProducts.length === 0
              ? 'var(--store-border-strong, #c5cad7)'
              : 'var(--store-accent, #172033)',
            color: '#ffffff',
            cursor: workspace.isBusy ? 'not-allowed' : 'pointer',
          }}
        >
          Assign first product to branch
        </button>

        {workspace.latestBranchCatalogItem ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest branch catalog item</h3>
            <DetailList
              items={[
                { label: 'Product', value: workspace.latestBranchCatalogItem.product_name },
                { label: 'MRP', value: String(workspace.latestBranchCatalogItem.mrp) },
                { label: 'Category', value: workspace.latestBranchCatalogItem.category_code ?? 'Unspecified' },
                { label: 'Tracking mode', value: workspace.latestBranchCatalogItem.tracking_mode },
                { label: 'Effective price', value: String(workspace.latestBranchCatalogItem.effective_selling_price) },
                { label: 'Status', value: <StatusBadge label={workspace.latestBranchCatalogItem.availability_status} tone="success" /> },
              ]}
            />
          </div>
        ) : null}

        <ul style={{ marginBottom: 0, marginTop: '16px', color: 'var(--store-text-muted, #5a6477)', lineHeight: 1.7 }}>
          {workspace.branchCatalogItems.map((item) => (
            <li key={item.id}>
              {item.product_name} {'->'} {item.effective_selling_price} :: MRP {item.mrp}
            </li>
          ))}
        </ul>
      </SectionCard>

      <OwnerBarcodeSection workspace={workspace} />
      <OwnerBarcodePrintRuntimeSection
        accessToken={workspace.accessToken}
        tenantId={workspace.tenantId}
        branchId={workspace.branchId}
        productId={workspace.catalogProducts[0]?.product_id ?? ''}
        devices={workspace.devices}
      />
    </>
  );
}

function OwnerCommercialScreen(props: { workspace: OwnerWorkspaceState }) {
  return (
    <>
      <OwnerBillingLifecycleSection accessToken={props.workspace.accessToken} tenantId={props.workspace.tenantId} />
      <OwnerPromotionCampaignSection accessToken={props.workspace.accessToken} tenantId={props.workspace.tenantId} />
      <OwnerGiftCardSection accessToken={props.workspace.accessToken} tenantId={props.workspace.tenantId} />
      <OwnerPriceTierSection workspace={props.workspace} />
      <OwnerCustomerInsightsSection
        accessToken={props.workspace.accessToken}
        tenantId={props.workspace.tenantId}
        branchId={props.workspace.branchId}
      />
      <OwnerBranchPerformanceSection
        accessToken={props.workspace.accessToken}
        tenantId={props.workspace.tenantId}
        branches={props.workspace.branches}
      />
    </>
  );
}

function OwnerOperationsScreen(props: { workspace: OwnerWorkspaceState }) {
  return (
    <>
      <OwnerProcurementSection workspace={props.workspace} />
      <OwnerReceivingSection workspace={props.workspace} />
      <OwnerBatchExpirySection workspace={props.workspace} />
      <OwnerProcurementFinanceSection workspace={props.workspace} />
      <OwnerInventoryControlSection workspace={props.workspace} />
      <OwnerReplenishmentSection workspace={props.workspace} />
      <OwnerRestockSection workspace={props.workspace} />
      <OwnerReturnApprovalsSection
        accessToken={props.workspace.accessToken}
        tenantId={props.workspace.tenantId}
        branchId={props.workspace.branchId}
      />
      <OwnerComplianceSection
        accessToken={props.workspace.accessToken}
        tenantId={props.workspace.tenantId}
        branchId={props.workspace.branchId}
      />
      <OwnerSupplierReportingSection
        accessToken={props.workspace.accessToken}
        tenantId={props.workspace.tenantId}
        branchId={props.workspace.branchId}
      />
      <OwnerSyncRuntimeSection
        accessToken={props.workspace.accessToken}
        tenantId={props.workspace.tenantId}
        branchId={props.workspace.branchId}
      />
    </>
  );
}

function OwnerWorkforceScreen(props: { workspace: OwnerWorkspaceState }) {
  const { workspace } = props;

  return (
    <>
      <SectionCard eyebrow="Membership bootstrap" title="Initial staff assignments">
        <FormField id="tenant-staff-email" label="Tenant staff email" value={workspace.tenantStaffEmail} onChange={workspace.setTenantStaffEmail} />
        <FormField
          id="tenant-staff-full-name"
          label="Tenant staff full name"
          value={workspace.tenantStaffFullName}
          onChange={workspace.setTenantStaffFullName}
        />
        <button
          type="button"
          onClick={() => void workspace.assignTenantRole()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.tenantStaffEmail || !workspace.tenantStaffFullName}
          style={{
            border: 0,
            borderRadius: 'var(--store-radius-pill, 999px)',
            padding: '11px 18px',
            fontSize: '14px',
            fontWeight: 700,
            background: workspace.isBusy || !workspace.actor || !workspace.tenantStaffEmail || !workspace.tenantStaffFullName
              ? 'var(--store-border-strong, #c5cad7)'
              : 'var(--store-accent, #172033)',
            color: '#ffffff',
            cursor: workspace.isBusy ? 'not-allowed' : 'pointer',
          }}
        >
          Assign tenant role
        </button>

        <div style={{ height: '16px' }} />

        <FormField id="branch-staff-email" label="Branch staff email" value={workspace.branchStaffEmail} onChange={workspace.setBranchStaffEmail} />
        <FormField
          id="branch-staff-full-name"
          label="Branch staff full name"
          value={workspace.branchStaffFullName}
          onChange={workspace.setBranchStaffFullName}
        />
        <button
          type="button"
          onClick={() => void workspace.assignBranchRole()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.branchId || !workspace.branchStaffEmail || !workspace.branchStaffFullName}
          style={{
            border: 0,
            borderRadius: 'var(--store-radius-pill, 999px)',
            padding: '11px 18px',
            fontSize: '14px',
            fontWeight: 700,
            background: workspace.isBusy || !workspace.actor || !workspace.branchId || !workspace.branchStaffEmail || !workspace.branchStaffFullName
              ? 'var(--store-border-strong, #c5cad7)'
              : 'var(--store-accent, #172033)',
            color: '#ffffff',
            cursor: workspace.isBusy ? 'not-allowed' : 'pointer',
          }}
        >
          Assign branch role
        </button>

        {workspace.latestTenantMembership ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest tenant membership</h3>
            <DetailList
              items={[
                { label: 'Email', value: workspace.latestTenantMembership.email },
                { label: 'Role', value: workspace.latestTenantMembership.role_name },
                { label: 'Status', value: <StatusBadge label={workspace.latestTenantMembership.status} tone="warning" /> },
              ]}
            />
          </div>
        ) : null}

        {workspace.latestBranchMembership ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest branch membership</h3>
            <DetailList
              items={[
                { label: 'Email', value: workspace.latestBranchMembership.email },
                { label: 'Role', value: workspace.latestBranchMembership.role_name },
                { label: 'Status', value: <StatusBadge label={workspace.latestBranchMembership.status} tone="warning" /> },
              ]}
            />
          </div>
        ) : null}
      </SectionCard>

      <SectionCard eyebrow="Staff foundation" title="Staff directory bootstrap">
        <FormField id="staff-profile-email" label="Staff profile email" value={workspace.staffProfileEmail} onChange={workspace.setStaffProfileEmail} />
        <FormField
          id="staff-profile-full-name"
          label="Staff profile full name"
          value={workspace.staffProfileFullName}
          onChange={workspace.setStaffProfileFullName}
        />
        <FormField id="staff-profile-phone" label="Staff profile phone" value={workspace.staffProfilePhone} onChange={workspace.setStaffProfilePhone} />
        <button
          type="button"
          onClick={() => void workspace.createStaffProfile()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.staffProfileEmail || !workspace.staffProfileFullName}
          style={{
            border: 0,
            borderRadius: 'var(--store-radius-pill, 999px)',
            padding: '11px 18px',
            fontSize: '14px',
            fontWeight: 700,
            background: workspace.isBusy || !workspace.actor || !workspace.staffProfileEmail || !workspace.staffProfileFullName
              ? 'var(--store-border-strong, #c5cad7)'
              : 'var(--store-accent, #172033)',
            color: '#ffffff',
            cursor: workspace.isBusy ? 'not-allowed' : 'pointer',
          }}
        >
          Create staff profile
        </button>

        {workspace.latestStaffProfile ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest staff profile</h3>
            <DetailList
              items={[
                { label: 'Email', value: workspace.latestStaffProfile.email },
                { label: 'Name', value: workspace.latestStaffProfile.full_name },
                { label: 'Status', value: <StatusBadge label={workspace.latestStaffProfile.status} tone="success" /> },
              ]}
            />
          </div>
        ) : null}

        <ul style={{ marginBottom: 0, marginTop: '16px', color: 'var(--store-text-muted, #5a6477)', lineHeight: 1.7 }}>
          {workspace.staffProfiles.map((profile) => (
            <li key={profile.id}>
              {profile.full_name}
              {profile.role_names.length > 0 ? ` (${profile.role_names.join(', ')})` : ''}
            </li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard eyebrow="Branch device foundation" title="Branch device registration">
        <FormField id="device-name" label="Device name" value={workspace.deviceName} onChange={workspace.setDeviceName} />
        <FormField id="device-code" label="Device code" value={workspace.deviceCode} onChange={workspace.setDeviceCode} />
        <button
          type="button"
          onClick={() => void workspace.registerBranchDevice()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.branchId || !workspace.deviceName || !workspace.deviceCode}
          style={{
            border: 0,
            borderRadius: 'var(--store-radius-pill, 999px)',
            padding: '11px 18px',
            fontSize: '14px',
            fontWeight: 700,
            background: workspace.isBusy || !workspace.actor || !workspace.branchId || !workspace.deviceName || !workspace.deviceCode
              ? 'var(--store-border-strong, #c5cad7)'
              : 'var(--store-accent, #172033)',
            color: '#ffffff',
            cursor: workspace.isBusy ? 'not-allowed' : 'pointer',
          }}
        >
          Register branch device
        </button>

        {workspace.latestDevice ? (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ marginBottom: '10px' }}>Latest branch device</h3>
            <DetailList
              items={[
                { label: 'Device code', value: workspace.latestDevice.device_code },
                { label: 'Surface', value: workspace.latestDevice.session_surface },
                { label: 'Status', value: <StatusBadge label={workspace.latestDevice.status} tone="success" /> },
              ]}
            />
          </div>
        ) : null}

        <ul style={{ marginBottom: 0, marginTop: '16px', color: 'var(--store-text-muted, #5a6477)', lineHeight: 1.7 }}>
          {workspace.devices.map((device) => (
            <li key={device.id}>
              {device.device_name}
              {device.assigned_staff_full_name ? ` -> ${device.assigned_staff_full_name}` : ''}
            </li>
          ))}
        </ul>
      </SectionCard>

      <OwnerRuntimePolicySection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />
      <OwnerShiftSessionSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />
      <OwnerAttendanceSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />
      <OwnerCashierSessionSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />
      <OwnerWorkforceAuditSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />
      <OwnerDeviceClaimSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />
    </>
  );
}

export function OwnerWorkspaceShell(props: { workspace: OwnerWorkspaceState }) {
  const [activeScreen, setActiveScreen] = useState<OwnerConsoleScreenId>('overview');
  const [branchScope, setBranchScope] = useState('all');
  const branchOptions = useMemo(() => {
    const branchItems = props.workspace.branches.map((branch) => ({ value: branch.branch_id, label: branch.name }));
    if (activeScreen === 'overview') {
      return [{ value: 'all', label: 'All branches' }, ...branchItems];
    }
    return branchItems;
  }, [activeScreen, props.workspace.branches]);

  useEffect(() => {
    if (activeScreen !== 'overview' && branchScope === 'all' && props.workspace.branchId) {
      setBranchScope(props.workspace.branchId);
      props.workspace.setSelectedBranchId(props.workspace.branchId);
    }
  }, [activeScreen, branchScope, props.workspace]);

  useEffect(() => {
    if (branchScope !== 'all' && branchScope !== props.workspace.selectedBranchId) {
      props.workspace.setSelectedBranchId(branchScope);
    }
  }, [branchScope, props.workspace]);

  useEffect(() => {
    if (props.workspace.selectedBranchId && activeScreen === 'overview' && branchScope !== 'all' && branchScope !== props.workspace.selectedBranchId) {
      setBranchScope(props.workspace.selectedBranchId);
    }
  }, [activeScreen, branchScope, props.workspace.selectedBranchId]);

  const screenCopy = SCREEN_COPY[activeScreen];
  const branchValue = activeScreen === 'overview' ? branchScope : props.workspace.branchId;

  let content = null;
  if (activeScreen === 'overview') {
    content = <OwnerOverviewScreen workspace={props.workspace} branchScope={branchScope} onSelectScreen={setActiveScreen} />;
  } else if (activeScreen === 'operations') {
    content = <OwnerOperationsScreen workspace={props.workspace} />;
  } else if (activeScreen === 'commercial') {
    content = <OwnerCommercialScreen workspace={props.workspace} />;
  } else if (activeScreen === 'catalog') {
    content = <OwnerCatalogScreen workspace={props.workspace} />;
  } else if (activeScreen === 'workforce') {
    content = <OwnerWorkforceScreen workspace={props.workspace} />;
  } else {
    content = <OwnerSettingsScreen workspace={props.workspace} />;
  }

  return (
    <OwnerCommandShell
      navRail={(
        <OwnerNavRail
          title={props.workspace.tenant?.name ?? 'Owner console'}
          subtitle={props.workspace.actor ? `${props.workspace.actor.full_name} · tenant owner` : 'Daily business command center'}
          items={OWNER_NAV_ITEMS}
          activeItemId={activeScreen}
          onSelect={(screenId) => setActiveScreen(screenId as OwnerConsoleScreenId)}
        />
      )}
      commandHeader={(
        <OwnerCommandHeader
          title={screenCopy.title}
          subtitle={screenCopy.subtitle}
          branchOptions={branchOptions}
          selectedBranch={branchValue || branchOptions[0]?.value || ''}
          onBranchChange={(value) => {
            setBranchScope(value);
            if (value !== 'all') {
              props.workspace.setSelectedBranchId(value);
            }
          }}
          actions={(
            <>
              <StatusBadge label={props.workspace.isBusy ? 'Working' : 'Live'} tone={props.workspace.isBusy ? 'warning' : 'success'} />
              <StoreThemeModeToggle />
            </>
          )}
        />
      )}
    >
      {content}
    </OwnerCommandShell>
  );
}
