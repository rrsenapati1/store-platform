import { DetailList, SectionCard, StatusBadge } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

export function StoreRuntimeCacheSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const cacheTone =
    workspace.cacheStatus === 'SYNCED'
      ? 'success'
      : workspace.cacheStatus === 'HYDRATED'
        ? 'warning'
        : 'neutral';
  const cacheLabel =
    workspace.cacheStatus === 'SYNCED'
      ? 'Synced'
      : workspace.cacheStatus === 'HYDRATED'
        ? 'Cached'
        : 'Empty';

  return (
    <SectionCard eyebrow="Local runtime cache" title="Cache boundary">
      <DetailList
        items={[
          { label: 'Session', value: workspace.isSessionLive ? 'Live' : workspace.cacheStatus === 'HYDRATED' ? 'Cached' : 'Not started' },
          { label: 'Authority', value: 'Control plane only' },
          { label: 'Cache backend', value: workspace.cacheBackendLabel },
          { label: 'Cache location', value: workspace.cacheBackendLocation ?? 'Runtime cache not mounted' },
          { label: 'Cache status', value: <StatusBadge label={cacheLabel} tone={cacheTone} /> },
          { label: 'Cached at', value: workspace.lastCachedAt ?? 'No cached snapshot yet' },
          { label: 'Pending cached mutations', value: String(workspace.pendingMutationCount) },
          { label: 'Backend note', value: workspace.cacheBackendDetail ?? 'Runtime cache stays non-authoritative and branch-local only.' },
        ]}
      />
      <p style={{ marginBottom: 0, color: '#4e5871' }}>
        Local runtime persistence is cache-only. It can hydrate the shell and retain branch posture, but it does not become the source of truth for stock, invoices, print completion, or any control-plane decision.
      </p>
    </SectionCard>
  );
}
