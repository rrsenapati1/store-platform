import { ActionButton, AppShell, DetailList, FormField, MetricGrid, SectionCard, StatusBadge } from '@store/ui';
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
import type { WorkspaceMetric } from '@store/types';
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
import { useOwnerWorkspace } from './useOwnerWorkspace';

function buildMetrics(branchCount: number, onboardingStatus: string | undefined, hasActor: boolean): WorkspaceMetric[] {
  return [
    { label: 'Branches', value: String(branchCount) },
    { label: 'Onboarding', value: onboardingStatus ?? 'Pending', tone: onboardingStatus === 'BRANCH_READY' ? 'success' : 'warning' },
    { label: 'Session', value: hasActor ? 'Live' : 'Not started', tone: hasActor ? 'success' : 'warning' },
  ];
}

export function OwnerWorkspace() {
  const workspace = useOwnerWorkspace();
  const branches = workspace.branches ?? [];
  const staffProfiles = workspace.staffProfiles ?? [];
  const catalogProducts = workspace.catalogProducts ?? [];
  const branchCatalogItems = workspace.branchCatalogItems ?? [];
  const devices = workspace.devices ?? [];
  const auditEvents = workspace.auditEvents ?? [];
  const metrics = buildMetrics(branches.length, workspace.tenant?.onboarding_status, Boolean(workspace.actor));

  return (
    <AppShell
      kicker="Tenant owner"
      title="Owner Onboarding Workspace"
      subtitle="First-branch setup, initial staff bootstrap, and onboarding audit visibility on the new control-plane service."
    >
      <MetricGrid metrics={metrics} />

      <SectionCard eyebrow="Owner session bootstrap" title="Tenant session">
        <FormField
          id="owner-korsenex-token"
          label="Korsenex token"
          value={workspace.korsenexToken}
          onChange={workspace.setKorsenexToken}
          placeholder="stub:sub=owner-1;email=owner@acme.local;name=Acme Owner"
        />
        <ActionButton onClick={() => void workspace.startSession()} disabled={workspace.isBusy || !workspace.korsenexToken}>
          Start owner session
        </ActionButton>
        {workspace.actor ? (
          <div style={{ marginTop: '16px' }}>
            <DetailList
              items={[
                { label: 'Actor', value: workspace.actor.full_name },
                { label: 'Email', value: workspace.actor.email },
                { label: 'Tenant', value: workspace.tenant?.name ?? 'Unbound' },
              ]}
            />
          </div>
        ) : null}
        {workspace.errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{workspace.errorMessage}</p> : null}
      </SectionCard>

      <SectionCard eyebrow="Tenant summary" title="Onboarding state">
        {workspace.tenant ? (
          <DetailList
            items={[
              { label: 'Tenant', value: workspace.tenant.name },
              { label: 'Slug', value: workspace.tenant.slug },
              { label: 'Status', value: <StatusBadge label={workspace.tenant.onboarding_status} tone={workspace.tenant.onboarding_status === 'BRANCH_READY' ? 'success' : 'warning'} /> },
            ]}
          />
        ) : (
          <p style={{ margin: 0, color: '#4e5871' }}>Start a session to load tenant onboarding.</p>
        )}
      </SectionCard>

      <OwnerBillingLifecycleSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} />
      <OwnerPromotionCampaignSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} />
      <OwnerGiftCardSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} />

      <SectionCard eyebrow="First branch setup" title="Branch creation">
        <FormField id="branch-name" label="Branch name" value={workspace.branchName} onChange={workspace.setBranchName} />
        <FormField id="branch-code" label="Branch code" value={workspace.branchCode} onChange={workspace.setBranchCode} />
        <FormField id="branch-gstin" label="Branch GSTIN" value={workspace.branchGstin} onChange={workspace.setBranchGstin} />
        <ActionButton
          onClick={() => void workspace.createFirstBranch()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.branchName || !workspace.branchCode}
        >
          Create first branch
        </ActionButton>
        <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {branches.map((branch) => (
            <li key={branch.branch_id}>{branch.name}</li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard eyebrow="Membership bootstrap" title="Initial staff assignments">
        <FormField id="tenant-staff-email" label="Tenant staff email" value={workspace.tenantStaffEmail} onChange={workspace.setTenantStaffEmail} />
        <FormField
          id="tenant-staff-full-name"
          label="Tenant staff full name"
          value={workspace.tenantStaffFullName}
          onChange={workspace.setTenantStaffFullName}
        />
        <ActionButton
          onClick={() => void workspace.assignTenantRole()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.tenantStaffEmail || !workspace.tenantStaffFullName}
        >
          Assign tenant role
        </ActionButton>

        <div style={{ height: '16px' }} />

        <FormField id="branch-staff-email" label="Branch staff email" value={workspace.branchStaffEmail} onChange={workspace.setBranchStaffEmail} />
        <FormField
          id="branch-staff-full-name"
          label="Branch staff full name"
          value={workspace.branchStaffFullName}
          onChange={workspace.setBranchStaffFullName}
        />
        <ActionButton
          onClick={() => void workspace.assignBranchRole()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.branchId || !workspace.branchStaffEmail || !workspace.branchStaffFullName}
        >
          Assign branch role
        </ActionButton>

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
        <ActionButton
          onClick={() => void workspace.createStaffProfile()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.staffProfileEmail || !workspace.staffProfileFullName}
        >
          Create staff profile
        </ActionButton>

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

        <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {staffProfiles.map((profile) => (
            <li key={profile.id}>
              {profile.full_name}
              {profile.role_names.length > 0 ? ` (${profile.role_names.join(', ')})` : ''}
            </li>
          ))}
        </ul>
      </SectionCard>

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
          <FormField
            id="product-minimum-age"
            label="Minimum age"
            value={workspace.productMinimumAge}
            onChange={workspace.setProductMinimumAge}
          />
        ) : null}
        <FormField id="product-selling-price" label="Selling price" value={workspace.productSellingPrice} onChange={workspace.setProductSellingPrice} />
        <ActionButton
          onClick={() => void workspace.createCatalogProduct()}
          disabled={
            workspace.isBusy ||
            !workspace.actor ||
            !workspace.productName ||
            !workspace.productSkuCode ||
            !workspace.productBarcode ||
            !workspace.productHsnSacCode ||
            !workspace.productMrp ||
            (workspace.productComplianceProfile === 'AGE_RESTRICTED' && !workspace.productMinimumAge) ||
            !workspace.productSellingPrice
          }
        >
          Create catalog product
        </ActionButton>

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

        <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {catalogProducts.map((product) => (
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
        <ActionButton
          onClick={() => void workspace.assignFirstProductToBranch()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.branchId || catalogProducts.length === 0}
        >
          Assign first product to branch
        </ActionButton>

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

        <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {branchCatalogItems.map((item) => (
            <li key={item.id}>
              {item.product_name} {'->'} {item.effective_selling_price} :: MRP {item.mrp}
            </li>
          ))}
        </ul>
      </SectionCard>

      <OwnerPriceTierSection workspace={workspace} />
      <OwnerBarcodeSection workspace={workspace} />
      <OwnerBarcodePrintRuntimeSection
        accessToken={workspace.accessToken}
        tenantId={workspace.tenantId}
        branchId={workspace.branchId}
        productId={catalogProducts[0]?.product_id ?? ''}
        devices={devices}
      />

      <OwnerProcurementSection workspace={workspace} />
      <OwnerReceivingSection workspace={workspace} />
      <OwnerBatchExpirySection workspace={workspace} />
      <OwnerProcurementFinanceSection workspace={workspace} />
      <OwnerInventoryControlSection workspace={workspace} />
      <OwnerReplenishmentSection workspace={workspace} />
      <OwnerRestockSection workspace={workspace} />
      <OwnerReturnApprovalsSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />
      <OwnerComplianceSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />
      <OwnerCustomerInsightsSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />
      <OwnerBranchPerformanceSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branches={branches} />
      <OwnerSupplierReportingSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />
      <OwnerSyncRuntimeSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />
      <OwnerRuntimePolicySection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />
      <OwnerShiftSessionSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />
      <OwnerAttendanceSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />
      <OwnerCashierSessionSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />
      <OwnerWorkforceAuditSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />
      <OwnerDeviceClaimSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />

      <SectionCard eyebrow="Branch device foundation" title="Branch device registration">
        <FormField id="device-name" label="Device name" value={workspace.deviceName} onChange={workspace.setDeviceName} />
        <FormField id="device-code" label="Device code" value={workspace.deviceCode} onChange={workspace.setDeviceCode} />
        <ActionButton
          onClick={() => void workspace.registerBranchDevice()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.branchId || !workspace.deviceName || !workspace.deviceCode}
        >
          Register branch device
        </ActionButton>

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

        <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {devices.map((device) => (
            <li key={device.id}>
              {device.device_name}
              {device.assigned_staff_full_name ? ` -> ${device.assigned_staff_full_name}` : ''}
            </li>
          ))}
        </ul>
      </SectionCard>

      <SectionCard eyebrow="Audit foundation" title="Onboarding audit feed">
        <ul style={{ marginBottom: 0, color: '#4e5871', lineHeight: 1.7 }}>
          {auditEvents.map((event) => (
            <li key={event.id}>{event.action}</li>
          ))}
        </ul>
      </SectionCard>
    </AppShell>
  );
}
