import { AppShell, DetailList, FormField, MetricGrid, SectionCard } from '@store/ui';
import { StoreBatchExpirySection } from './StoreBatchExpirySection';
import { StoreBarcodeLookupSection } from './StoreBarcodeLookupSection';
import type { WorkspaceMetric } from '@store/types';
import { StoreBillingSection } from './StoreBillingSection';
import { StoreCustomerInsightsSection } from './StoreCustomerInsightsSection';
import { StoreRuntimeCacheSection } from './StoreRuntimeCacheSection';
import { StoreRuntimeOutboxSection } from './StoreRuntimeOutboxSection';
import { StoreExchangeSection } from './StoreExchangeSection';
import { StorePrintQueueSection } from './StorePrintQueueSection';
import { StoreReturnsSection } from './StoreReturnsSection';
import { StoreRuntimeShellSection } from './StoreRuntimeShellSection';
import { StoreSupplierReportingSection } from './StoreSupplierReportingSection';
import { StoreSyncRuntimeSection } from './StoreSyncRuntimeSection';
import { useStoreRuntimeWorkspace } from './useStoreRuntimeWorkspace';

function buildMetrics(args: { branchCount: number; isSessionLive: boolean; cacheStatus: 'EMPTY' | 'HYDRATED' | 'SYNCED'; stockRecords: number }): WorkspaceMetric[] {
  return [
    {
      label: 'Session',
      value: args.isSessionLive ? 'Live' : args.cacheStatus === 'HYDRATED' ? 'Cached' : 'Not started',
      tone: args.isSessionLive ? 'success' : args.cacheStatus === 'HYDRATED' ? 'warning' : 'warning',
    },
    { label: 'Branches', value: String(args.branchCount) },
    { label: 'Stock records', value: String(args.stockRecords) },
  ];
}

export function StoreRuntimeWorkspace() {
  const workspace = useStoreRuntimeWorkspace();
  const metrics = buildMetrics({
    branchCount: workspace.branches.length,
    isSessionLive: workspace.isSessionLive,
    cacheStatus: workspace.cacheStatus,
    stockRecords: workspace.inventorySnapshot.length,
  });

  return (
    <AppShell
      kicker="Store runtime"
      title="Store Runtime"
      subtitle="Branch-scoped checkout posture on the new control-plane billing foundation."
    >
      <MetricGrid metrics={metrics} />

      <StoreRuntimeShellSection workspace={workspace} />
      <StoreRuntimeCacheSection workspace={workspace} />
      <StoreRuntimeOutboxSection workspace={workspace} />

      <SectionCard eyebrow="Runtime session bootstrap" title="Store session">
        <FormField
          id="store-korsenex-token"
          label="Korsenex token"
          value={workspace.korsenexToken}
          onChange={workspace.setKorsenexToken}
          placeholder="stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier"
        />
        <button
          type="button"
          onClick={() => void workspace.startSession()}
          disabled={workspace.isBusy || !workspace.korsenexToken}
          style={{
            border: 0,
            borderRadius: '999px',
            padding: '11px 18px',
            fontSize: '14px',
            fontWeight: 700,
            background: workspace.isBusy || !workspace.korsenexToken ? '#c5cad7' : '#172033',
            color: '#ffffff',
            cursor: workspace.isBusy || !workspace.korsenexToken ? 'not-allowed' : 'pointer',
          }}
        >
          Start runtime session
        </button>

        {workspace.actor ? (
          <div style={{ marginTop: '16px' }}>
            <DetailList
              items={[
                { label: 'Actor', value: workspace.actor.full_name },
                { label: 'Email', value: workspace.actor.email },
                { label: 'Tenant', value: workspace.tenant?.name ?? 'Unbound' },
                { label: 'Branch', value: workspace.branches[0]?.name ?? workspace.branchId ?? 'Unbound' },
                { label: 'Runtime authority', value: 'Control plane only' },
              ]}
            />
          </div>
        ) : null}
        {workspace.errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{workspace.errorMessage}</p> : null}
      </SectionCard>

      <StoreBillingSection workspace={workspace} />
      <StoreBarcodeLookupSection workspace={workspace} />
      <StoreBatchExpirySection workspace={workspace} />
      <StorePrintQueueSection workspace={workspace} />
      <StoreReturnsSection workspace={workspace} />
      <StoreSupplierReportingSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />
      <StoreSyncRuntimeSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />
      <StoreCustomerInsightsSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} />
      <StoreExchangeSection workspace={workspace} />
    </AppShell>
  );
}
