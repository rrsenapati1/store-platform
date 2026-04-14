import { DetailList, SectionCard, StatusBadge } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function buildPlatformLabel(operatingSystem: string | null, architecture: string | null) {
  if (operatingSystem && architecture) {
    return `${operatingSystem} / ${architecture}`;
  }
  if (operatingSystem) {
    return operatingSystem;
  }
  if (architecture) {
    return architecture;
  }
  return 'Browser-managed';
}

function buildBridgeTone(bridgeState: StoreRuntimeWorkspaceState['runtimeShellBridgeState']) {
  if (bridgeState === 'ready') {
    return 'success';
  }
  if (bridgeState === 'unavailable') {
    return 'neutral';
  }
  return 'warning';
}

function buildBridgeLabel(bridgeState: StoreRuntimeWorkspaceState['runtimeShellBridgeState']) {
  if (bridgeState === 'ready') {
    return 'Ready';
  }
  if (bridgeState === 'unavailable') {
    return 'Unavailable';
  }
  return 'Browser fallback';
}

function buildBindingTone(bindingStatus: StoreRuntimeWorkspaceState['runtimeBindingStatus']) {
  if (bindingStatus === 'APPROVED') {
    return 'success';
  }
  if (bindingStatus === 'PENDING') {
    return 'warning';
  }
  return 'neutral';
}

export function StoreRuntimeShellSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  return (
    <SectionCard eyebrow="Packaged runtime shell" title="Shell identity">
      <DetailList
        items={[
          { label: 'Runtime mode', value: workspace.runtimeShellLabel ?? 'Resolving runtime shell...' },
          {
            label: 'Bridge state',
            value: <StatusBadge label={buildBridgeLabel(workspace.runtimeShellBridgeState)} tone={buildBridgeTone(workspace.runtimeShellBridgeState)} />,
          },
          {
            label: 'Binding status',
            value: <StatusBadge label={workspace.runtimeBindingStatus} tone={buildBindingTone(workspace.runtimeBindingStatus)} />,
          },
          { label: 'Installation fingerprint', value: workspace.runtimeInstallationId ?? 'Browser-managed' },
          { label: 'Claim code', value: workspace.runtimeClaimCode ?? 'Browser-managed' },
          { label: 'Hostname', value: workspace.runtimeHostname ?? 'Unavailable' },
          { label: 'Platform', value: buildPlatformLabel(workspace.runtimeOperatingSystem, workspace.runtimeArchitecture) },
          { label: 'App version', value: workspace.runtimeAppVersion ?? 'Web dev shell' },
          { label: 'Runtime home', value: workspace.runtimeHome ?? 'Browser-managed' },
          { label: 'Cache database', value: workspace.runtimeCacheDatabasePath ?? 'Browser-managed' },
        ]}
      />
      <p style={{ marginBottom: 0, color: '#4e5871' }}>
        This surface is read-only shell posture. It identifies the active runtime container and its stable installation fingerprint, but it does not replace control-plane device registration or branch authority.
      </p>
      {workspace.runtimeShellError ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{workspace.runtimeShellError}</p> : null}
    </SectionCard>
  );
}
