import { AppShell, DetailList, FormField, MetricGrid, SectionCard } from '@store/ui';
import { StoreBatchExpirySection } from './StoreBatchExpirySection';
import { StoreBarcodeLookupSection } from './StoreBarcodeLookupSection';
import type { WorkspaceMetric } from '@store/types';
import { StoreBillingSection } from './StoreBillingSection';
import { StoreCustomerInsightsSection } from './StoreCustomerInsightsSection';
import { StoreCustomerDisplaySection } from './StoreCustomerDisplaySection';
import { StoreOfflineContinuitySection } from './StoreOfflineContinuitySection';
import { StoreRuntimeCacheSection } from './StoreRuntimeCacheSection';
import { StoreRuntimeOutboxSection } from './StoreRuntimeOutboxSection';
import { StoreExchangeSection } from './StoreExchangeSection';
import { StorePrintQueueSection } from './StorePrintQueueSection';
import { StoreRestockSection } from './StoreRestockSection';
import { StoreRuntimeReleaseSection } from './StoreRuntimeReleaseSection';
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
  const branches = workspace.branches ?? [];
  const inventorySnapshot = workspace.inventorySnapshot ?? [];
  const cacheStatus = workspace.cacheStatus ?? 'EMPTY';
  const showPackagedActivation = workspace.runtimeShellKind === 'packaged_desktop'
    && !workspace.isSessionLive
    && !workspace.requiresPinEnrollment
    && !workspace.requiresLocalUnlock
    && workspace.hasLoadedLocalAuth;
  const isLocalAuthGateActive = workspace.runtimeShellKind === 'packaged_desktop'
    && (!workspace.hasLoadedLocalAuth || workspace.requiresPinEnrollment || workspace.requiresLocalUnlock);
  const metrics = buildMetrics({
    branchCount: isLocalAuthGateActive ? 0 : branches.length,
    isSessionLive: !isLocalAuthGateActive && workspace.isSessionLive,
    cacheStatus: isLocalAuthGateActive ? 'EMPTY' : cacheStatus,
    stockRecords: isLocalAuthGateActive ? 0 : inventorySnapshot.length,
  });

  return (
    <AppShell
      kicker="Store runtime"
      title="Store Runtime"
      subtitle="Branch-scoped checkout posture on the new control-plane billing foundation."
    >
      <MetricGrid metrics={metrics} />

      <StoreRuntimeShellSection workspace={workspace} />
      <StoreRuntimeReleaseSection />
      {!isLocalAuthGateActive ? <StoreRuntimeCacheSection workspace={workspace} /> : null}
      {!isLocalAuthGateActive ? <StoreRuntimeOutboxSection workspace={workspace} /> : null}

      <SectionCard eyebrow="Runtime session bootstrap" title="Store session">
        {!workspace.hasLoadedLocalAuth && workspace.runtimeShellKind === 'packaged_desktop' ? (
          <p style={{ color: '#4e5871', marginBottom: 0 }}>
            Checking device-bound runtime access for this packaged desktop.
          </p>
        ) : workspace.requiresPinEnrollment ? (
          <>
            <h3 style={{ marginTop: 0, marginBottom: '12px' }}>Set runtime PIN</h3>
            <FormField
              id="store-runtime-new-pin"
              label="New PIN"
              value={workspace.newPin}
              onChange={workspace.setNewPin}
              placeholder="2580"
            />
            <FormField
              id="store-runtime-confirm-pin"
              label="Confirm PIN"
              value={workspace.confirmPin}
              onChange={workspace.setConfirmPin}
              placeholder="2580"
            />
            <button
              type="button"
              onClick={() => void workspace.enrollRuntimePin()}
              disabled={workspace.isBusy || !workspace.newPin || !workspace.confirmPin}
              style={{
                border: 0,
                borderRadius: '999px',
                padding: '11px 18px',
                fontSize: '14px',
                fontWeight: 700,
                background: workspace.isBusy || !workspace.newPin || !workspace.confirmPin ? '#c5cad7' : '#172033',
                color: '#ffffff',
                cursor: workspace.isBusy || !workspace.newPin || !workspace.confirmPin ? 'not-allowed' : 'pointer',
              }}
            >
              Save runtime PIN
            </button>
            <p style={{ color: '#4e5871', marginBottom: 0 }}>
              This PIN only unlocks this approved packaged device and never acts as a web credential.
            </p>
          </>
        ) : workspace.requiresLocalUnlock ? (
          <>
            <h3 style={{ marginTop: 0, marginBottom: '12px' }}>Unlock with PIN</h3>
            <FormField
              id="store-runtime-unlock-pin"
              label="PIN"
              value={workspace.unlockPin}
              onChange={workspace.setUnlockPin}
              placeholder="2580"
            />
            <button
              type="button"
              onClick={() => void workspace.unlockRuntimeWithPin()}
              disabled={workspace.isBusy || !workspace.unlockPin}
              style={{
                border: 0,
                borderRadius: '999px',
                padding: '11px 18px',
                fontSize: '14px',
                fontWeight: 700,
                background: workspace.isBusy || !workspace.unlockPin ? '#c5cad7' : '#172033',
                color: '#ffffff',
                cursor: workspace.isBusy || !workspace.unlockPin ? 'not-allowed' : 'pointer',
              }}
            >
              Unlock runtime
            </button>
            <p style={{ color: '#4e5871', marginBottom: 0 }}>
              Use the device PIN that was enrolled after owner activation.
            </p>
          </>
        ) : showPackagedActivation ? (
          <>
            <h3 style={{ marginTop: 0, marginBottom: '12px' }}>Desktop activation</h3>
            <FormField
              id="store-desktop-activation-code"
              label="Activation code"
              value={workspace.activationCode}
              onChange={workspace.setActivationCode}
              placeholder="ACTV-1234-5678"
            />
            <button
              type="button"
              onClick={() => void workspace.activateDesktopAccess()}
              disabled={workspace.isBusy || !workspace.activationCode}
              style={{
                border: 0,
                borderRadius: '999px',
                padding: '11px 18px',
                fontSize: '14px',
                fontWeight: 700,
                background: workspace.isBusy || !workspace.activationCode ? '#c5cad7' : '#172033',
                color: '#ffffff',
                cursor: workspace.isBusy || !workspace.activationCode ? 'not-allowed' : 'pointer',
              }}
            >
              Activate desktop access
            </button>
            <p style={{ color: '#4e5871', marginBottom: 0 }}>
              Desktop activation
              {' '}requires an owner-issued code for this approved packaged runtime.
            </p>
          </>
        ) : workspace.supportsDeveloperSessionBootstrap ? (
          <>
            <h3 style={{ marginTop: 0, marginBottom: '12px' }}>Developer session bootstrap</h3>
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
            <p style={{ color: '#4e5871', marginBottom: 0 }}>
              This browser-only bootstrap remains available for local development and tests, not for production operator sign-in.
            </p>
          </>
        ) : (
          <p style={{ color: '#4e5871', marginBottom: 0 }}>
            Browser preview does not support production sign-in. Use the approved packaged desktop activation flow for operator access.
          </p>
        )}

        {workspace.actor && !isLocalAuthGateActive ? (
          <div style={{ marginTop: '16px' }}>
            <DetailList
              items={[
                { label: 'Actor', value: workspace.actor.full_name },
                { label: 'Email', value: workspace.actor.email },
                { label: 'Tenant', value: workspace.tenant?.name ?? 'Unbound' },
                { label: 'Branch', value: branches[0]?.name ?? workspace.branchId ?? 'Unbound' },
                { label: 'Session expires', value: workspace.sessionExpiresAt ?? 'Unknown' },
                { label: 'Runtime authority', value: 'Control plane only' },
              ]}
            />
            <button
              type="button"
              onClick={() => void workspace.refreshRuntimeSession()}
              disabled={workspace.isBusy || !workspace.isSessionLive}
              style={{
                border: 0,
                borderRadius: '999px',
                padding: '11px 18px',
                fontSize: '14px',
                fontWeight: 700,
                marginTop: '16px',
                marginRight: '12px',
                background: workspace.isBusy || !workspace.isSessionLive ? '#c5cad7' : '#172033',
                color: '#ffffff',
                cursor: workspace.isBusy || !workspace.isSessionLive ? 'not-allowed' : 'pointer',
              }}
            >
              Refresh runtime session
            </button>
            <button
              type="button"
              onClick={() => void workspace.signOut()}
              disabled={workspace.isBusy}
              style={{
                border: 0,
                borderRadius: '999px',
                padding: '11px 18px',
                fontSize: '14px',
                fontWeight: 700,
                marginTop: '16px',
                background: workspace.isBusy ? '#c5cad7' : '#7f1d1d',
                color: '#ffffff',
                cursor: workspace.isBusy ? 'not-allowed' : 'pointer',
              }}
            >
              Sign out
            </button>
          </div>
        ) : null}
        {workspace.errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{workspace.errorMessage}</p> : null}
      </SectionCard>

      {!isLocalAuthGateActive ? <StoreOfflineContinuitySection workspace={workspace} /> : null}
      {!isLocalAuthGateActive ? <StoreCustomerDisplaySection workspace={workspace} /> : null}
      {!isLocalAuthGateActive ? <StoreBillingSection workspace={workspace} /> : null}
      {!isLocalAuthGateActive ? <StoreBarcodeLookupSection workspace={workspace} /> : null}
      {!isLocalAuthGateActive ? <StoreRestockSection workspace={workspace} /> : null}
      {!isLocalAuthGateActive ? <StoreBatchExpirySection workspace={workspace} /> : null}
      {!isLocalAuthGateActive ? <StorePrintQueueSection workspace={workspace} /> : null}
      {!isLocalAuthGateActive ? <StoreReturnsSection workspace={workspace} /> : null}
      {!isLocalAuthGateActive ? <StoreSupplierReportingSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} /> : null}
      {!isLocalAuthGateActive ? (
        <StoreSyncRuntimeSection
          accessToken={workspace.accessToken}
          tenantId={workspace.tenantId}
          branchId={workspace.branchId}
          runtimeHubServiceUrl={workspace.runtimeHubServiceUrl}
          runtimeHubManifestUrl={workspace.runtimeHubManifestUrl}
        />
      ) : null}
      {!isLocalAuthGateActive ? <StoreCustomerInsightsSection accessToken={workspace.accessToken} tenantId={workspace.tenantId} branchId={workspace.branchId} /> : null}
      {!isLocalAuthGateActive ? <StoreExchangeSection workspace={workspace} /> : null}
    </AppShell>
  );
}
