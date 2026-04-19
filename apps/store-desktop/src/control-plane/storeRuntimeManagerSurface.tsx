import type { CSSProperties } from 'react';
import { SectionCard } from '@store/ui';
import { StoreBranchDecisionSupportSection } from './StoreBranchDecisionSupportSection';
import { StoreBranchOperationsDashboardSection } from './StoreBranchOperationsDashboardSection';
import { StoreCustomerInsightsSection } from './StoreCustomerInsightsSection';
import { StoreShiftSection } from './StoreShiftSection';
import { StoreSupplierReportingSection } from './StoreSupplierReportingSection';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

const surfaceGridStyle: CSSProperties = {
  display: 'grid',
  gap: '16px',
  gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
  alignItems: 'start',
};

export function StoreRuntimeManagerSurface({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const accessToken = workspace.accessToken;
  const tenantId = workspace.tenantId;
  const branchId = workspace.branchId;

  return (
    <div style={{ display: 'grid', gap: '16px' }}>
      <SectionCard eyebrow="Branch management" title="Manager cockpit">
        <p style={{ margin: 0, color: '#4e5871' }}>
          Review branch posture, shift governance, customer signals, and supplier exposure without the full operational stack.
        </p>
      </SectionCard>

      <div style={surfaceGridStyle}>
        <StoreBranchOperationsDashboardSection workspace={workspace} />
        <StoreBranchDecisionSupportSection accessToken={accessToken ?? ''} tenantId={tenantId ?? ''} branchId={branchId ?? ''} />
        <StoreShiftSection workspace={workspace} />
        <StoreCustomerInsightsSection accessToken={accessToken ?? ''} tenantId={tenantId ?? ''} branchId={branchId ?? ''} />
        <div style={{ gridColumn: '1 / -1' }}>
          <StoreSupplierReportingSection accessToken={accessToken ?? ''} tenantId={tenantId ?? ''} branchId={branchId ?? ''} />
        </div>
      </div>
    </div>
  );
}
