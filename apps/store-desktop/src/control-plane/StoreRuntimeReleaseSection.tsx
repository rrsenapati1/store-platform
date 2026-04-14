import { useMemo, useState } from 'react';
import { DetailList, SectionCard, StatusBadge } from '@store/ui';
import { createResolvedStoreRuntimeUpdater, type StoreRuntimeUpdateCheckResult, type StoreRuntimeUpdateInstallResult } from '../runtime-updater/storeRuntimeUpdater';
import { useStoreRuntimeShellStatus } from './useStoreRuntimeShellStatus';

function buildReleaseTone(value: string | null) {
  if (value === 'prod') {
    return 'success';
  }
  if (value === 'staging') {
    return 'warning';
  }
  return 'neutral';
}

function buildUpdateStatusLabel(checkResult: StoreRuntimeUpdateCheckResult | null, installResult: StoreRuntimeUpdateInstallResult | null) {
  if (installResult?.state === 'installed') {
    return `Installed ${installResult.installed_version ?? 'update'}`;
  }
  if (checkResult?.state === 'update_available') {
    return `Available ${checkResult.update_version ?? 'update'}`;
  }
  if (checkResult?.state === 'up_to_date') {
    return 'Up to date';
  }
  if (checkResult?.state === 'unconfigured') {
    return 'Unconfigured';
  }
  return 'Packaged runtime only';
}

function buildUpdateStatusTone(checkResult: StoreRuntimeUpdateCheckResult | null, installResult: StoreRuntimeUpdateInstallResult | null) {
  if (installResult?.state === 'installed') {
    return 'success';
  }
  if (checkResult?.state === 'update_available') {
    return 'warning';
  }
  if (checkResult?.state === 'up_to_date') {
    return 'success';
  }
  return 'neutral';
}

export function StoreRuntimeReleaseSection() {
  const { runtimeShellError, runtimeShellStatus } = useStoreRuntimeShellStatus();
  const updater = useMemo(() => createResolvedStoreRuntimeUpdater(), []);
  const [checkResult, setCheckResult] = useState<StoreRuntimeUpdateCheckResult | null>(null);
  const [installResult, setInstallResult] = useState<StoreRuntimeUpdateInstallResult | null>(null);
  const [busyAction, setBusyAction] = useState<'check' | 'install' | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  async function checkForUpdates() {
    setBusyAction('check');
    setActionError(null);
    try {
      const result = await updater.check();
      setCheckResult(result);
      setInstallResult(null);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Unable to check for runtime updates.');
    } finally {
      setBusyAction(null);
    }
  }

  async function installUpdate() {
    setBusyAction('install');
    setActionError(null);
    try {
      const result = await updater.install();
      setInstallResult(result);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'Unable to install the pending runtime update.');
    } finally {
      setBusyAction(null);
    }
  }

  const packagedRuntime = runtimeShellStatus?.runtime_kind === 'packaged_desktop';
  const canCheckUpdates = packagedRuntime && busyAction === null;
  const canInstallUpdate = packagedRuntime && busyAction === null && checkResult?.state === 'update_available';

  return (
    <SectionCard eyebrow="Packaging + distribution" title="Release channel">
      <DetailList
        items={[
          {
            label: 'Release environment',
            value: runtimeShellStatus?.release_environment ? (
              <StatusBadge
                label={runtimeShellStatus.release_environment}
                tone={buildReleaseTone(runtimeShellStatus.release_environment)}
              />
            ) : 'Browser-managed',
          },
          { label: 'Profile source', value: runtimeShellStatus?.release_profile_source ?? 'Browser-managed' },
          { label: 'Control-plane origin', value: runtimeShellStatus?.control_plane_base_url ?? 'Browser-managed' },
          { label: 'Update feed', value: runtimeShellStatus?.updater_endpoint ?? 'Not configured' },
          {
            label: 'Updater signature key',
            value: runtimeShellStatus?.updater_pubkey_configured ? 'Configured' : 'Not configured',
          },
          {
            label: 'Update status',
            value: <StatusBadge label={buildUpdateStatusLabel(checkResult, installResult)} tone={buildUpdateStatusTone(checkResult, installResult)} />,
          },
          { label: 'Current app version', value: runtimeShellStatus?.app_version ?? 'Browser shell' },
        ]}
      />
      <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
        <button
          type="button"
          onClick={() => void checkForUpdates()}
          disabled={!canCheckUpdates}
          style={{
            border: 0,
            borderRadius: '999px',
            padding: '11px 18px',
            fontSize: '14px',
            fontWeight: 700,
            background: canCheckUpdates ? '#172033' : '#c5cad7',
            color: '#ffffff',
            cursor: canCheckUpdates ? 'pointer' : 'not-allowed',
          }}
        >
          {busyAction === 'check' ? 'Checking updates…' : 'Check for updates'}
        </button>
        <button
          type="button"
          onClick={() => void installUpdate()}
          disabled={!canInstallUpdate}
          style={{
            border: 0,
            borderRadius: '999px',
            padding: '11px 18px',
            fontSize: '14px',
            fontWeight: 700,
            background: canInstallUpdate ? '#7f1d1d' : '#c5cad7',
            color: '#ffffff',
            cursor: canInstallUpdate ? 'pointer' : 'not-allowed',
          }}
        >
          {busyAction === 'install' ? 'Installing update…' : 'Install pending update'}
        </button>
      </div>
      <p style={{ color: '#4e5871', marginBottom: 0 }}>
        Packaged Store Desktop installers should be built against an explicit release profile instead of inheriting machine-local environment defaults after installation.
      </p>
      {checkResult?.notes ? <p style={{ color: '#4e5871', marginBottom: 0 }}>Release notes: {checkResult.notes}</p> : null}
      {installResult?.state === 'installed' ? (
        <p style={{ color: '#4e5871', marginBottom: 0 }}>
          Update payload downloaded. Restart the packaged runtime after the installer finishes applying the new version.
        </p>
      ) : null}
      {runtimeShellError ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{runtimeShellError}</p> : null}
      {actionError ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{actionError}</p> : null}
      {checkResult?.error ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{checkResult.error}</p> : null}
      {installResult?.error ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{installResult.error}</p> : null}
    </SectionCard>
  );
}
