import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import { StoreAttendanceSection } from './StoreAttendanceSection';
import { StoreCashierSessionSection } from './StoreCashierSessionSection';
import { StoreShiftSection } from './StoreShiftSection';
import { StoreRuntimeReleaseSection } from './StoreRuntimeReleaseSection';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function resolveEntryCtaState(workspace: StoreRuntimeWorkspaceState) {
  const selectedRuntimeDevice = workspace.runtimeDevices.find((device) => device.id === workspace.selectedRuntimeDeviceId)
    ?? workspace.runtimeDevices[0]
    ?? null;
  const requiresShift = workspace.branchRuntimePolicy?.require_shift_for_attendance ?? false;
  const requiresAttendance = workspace.branchRuntimePolicy?.require_attendance_for_cashier ?? true;
  const shiftGateSatisfied = !requiresShift || Boolean(workspace.activeShiftSession);
  const attendanceGateSatisfied = !requiresAttendance || Boolean(workspace.activeAttendanceSession);
  const canClockIn = Boolean(workspace.isSessionLive && selectedRuntimeDevice?.assigned_staff_profile_id && shiftGateSatisfied);
  const canOpenRegister = Boolean(
    workspace.isSessionLive
      && selectedRuntimeDevice?.assigned_staff_profile_id
      && workspace.cashierOpeningFloatAmount !== ''
      && attendanceGateSatisfied,
  );
  const canResumeSelling = Boolean(workspace.isSessionLive && workspace.activeCashierSession);

  return {
    selectedRuntimeDevice,
    requiresShift,
    requiresAttendance,
    canClockIn,
    canOpenRegister,
    canResumeSelling,
  };
}

function resolveEntrySurfaceCopy(workspace: StoreRuntimeWorkspaceState) {
  if (workspace.requiresPinEnrollment) {
    return {
      eyebrow: 'Runtime security',
      body: 'Create a 4-digit PIN so this approved terminal can resume securely after the initial activation.',
      title: 'Protect this terminal',
    };
  }
  if (workspace.requiresLocalUnlock) {
    if (workspace.runtimeSessionStatus === 'expired') {
      return {
        eyebrow: 'Session recovery',
        body: 'The previous runtime session expired. Unlock this device to fetch a fresh session or recover cached runtime access.',
        title: 'Runtime session expired',
      };
    }
    if (workspace.runtimeSessionStatus === 'revoked') {
      return {
        eyebrow: 'Session recovery',
        body: 'This device session was revoked. Unlock will not recover access; a fresh owner-issued activation is required.',
        title: 'Runtime access revoked',
      };
    }
    if (workspace.runtimeSessionStatus === 'signed_out_on_device') {
      return {
        eyebrow: 'Signed out',
        body: 'The live session ended on this approved terminal. Unlock with the device PIN to resume operator access.',
        title: 'Unlock this terminal',
      };
    }
    return {
      eyebrow: 'Device unlock',
      body: 'This packaged terminal is approved for store use. Unlock it locally before resuming branch operations.',
      title: 'Unlock this terminal',
    };
  }
  if (workspace.runtimeShellKind === 'packaged_desktop') {
    if (workspace.runtimeSessionStatus === 'revoked') {
      return {
        eyebrow: 'Activation required',
        body: 'The previous runtime grant is no longer valid on this machine. Ask the owner to issue a fresh activation code.',
        title: 'Runtime access revoked',
      };
    }
    if (workspace.runtimeSessionStatus === 'commercial_hold') {
      return {
        eyebrow: 'Commercial hold',
        body: 'This tenant cannot activate new runtime sessions until billing access is restored.',
        title: 'Activation blocked',
      };
    }
    return {
      eyebrow: 'Device activation',
      body: 'Activate this packaged desktop once, then continue with PIN unlock and cashier session controls on future launches.',
      title: 'Activate this terminal',
    };
  }
  if (workspace.supportsDeveloperSessionBootstrap) {
    return {
      eyebrow: 'Developer bootstrap',
      body: 'Local browser preview can still bootstrap a runtime session for development and UI verification.',
      title: 'Sign in to this runtime',
    };
  }
  return {
    eyebrow: 'Browser preview',
    body: 'Browser preview does not support production sign-in. Use the packaged desktop activation flow for operator access.',
    title: 'Preview-only runtime',
  };
}

export function StoreRuntimeEntrySurface(
  props: { workspace: StoreRuntimeWorkspaceState; onResumeSelling: () => void },
) {
  const { workspace } = props;
  const isIdentityLocked = workspace.runtimeShellKind === 'packaged_desktop'
    && !workspace.isSessionLive
    && (workspace.requiresLocalUnlock || workspace.requiresPinEnrollment);
  const showPackagedActivation = workspace.runtimeShellKind === 'packaged_desktop'
    && !workspace.isSessionLive
    && !workspace.requiresPinEnrollment
    && !workspace.requiresLocalUnlock
    && workspace.hasLoadedLocalAuth;
  const ctaState = resolveEntryCtaState(workspace);
  const copy = resolveEntrySurfaceCopy(workspace);

  return (
    <div
      style={{
        display: 'grid',
        gap: '24px',
        gridTemplateColumns: 'minmax(0, 1.4fr) minmax(320px, 0.9fr)',
      }}
    >
      <div style={{ display: 'grid', gap: '24px' }}>
        <SectionCard eyebrow="Entry" title="Store access">
          <p style={{ marginTop: 0, marginBottom: '10px', fontSize: '12px', letterSpacing: '0.12em', textTransform: 'uppercase', color: '#75809b' }}>
            {copy.eyebrow}
          </p>
          <h3 style={{ marginTop: 0, marginBottom: '10px', fontSize: '24px', color: '#172033' }}>{copy.title}</h3>
          <p style={{ marginTop: 0, color: '#4e5871' }}>{copy.body}</p>
              <DetailList
            items={[
              { label: 'Runtime', value: workspace.runtimeShellLabel ?? 'Resolving runtime shell...' },
              { label: 'Hostname', value: workspace.runtimeHostname ?? 'Browser-managed' },
              { label: 'Actor', value: isIdentityLocked ? 'Locked until PIN unlock' : workspace.actor?.full_name ?? 'Signed out' },
              {
                label: 'Session',
                value: workspace.isSessionLive ? <StatusBadge label="Live" tone="success" /> : <StatusBadge label="Idle" tone="neutral" />,
              },
              { label: 'Branch', value: workspace.branches?.[0]?.name ?? workspace.branchId ?? 'Unbound' },
              { label: 'Device', value: ctaState.selectedRuntimeDevice?.device_name ?? 'No runtime device selected' },
            ]}
          />

          <div style={{ marginTop: '18px' }}>
            {!workspace.hasLoadedLocalAuth && workspace.runtimeShellKind === 'packaged_desktop' ? (
              <p style={{ color: '#4e5871', marginBottom: 0 }}>
                Checking device-bound runtime access for this packaged desktop.
              </p>
            ) : workspace.requiresPinEnrollment ? (
              <div style={{ display: 'grid', gap: '12px' }}>
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
                <ActionButton
                  onClick={() => void workspace.enrollRuntimePin()}
                  disabled={workspace.isBusy || !workspace.newPin || !workspace.confirmPin}
                >
                  Save runtime PIN
                </ActionButton>
              </div>
            ) : workspace.requiresLocalUnlock ? (
              <div style={{ display: 'grid', gap: '12px' }}>
                <FormField
                  id="store-runtime-unlock-pin"
                  label="PIN"
                  value={workspace.unlockPin}
                  onChange={workspace.setUnlockPin}
                  placeholder="2580"
                />
                <ActionButton
                  onClick={() => void workspace.unlockRuntimeWithPin()}
                  disabled={workspace.isBusy || !workspace.unlockPin}
                >
                  Unlock runtime
                </ActionButton>
              </div>
            ) : showPackagedActivation ? (
              <div style={{ display: 'grid', gap: '12px' }}>
                <FormField
                  id="store-desktop-activation-code"
                  label="Activation code"
                  value={workspace.activationCode}
                  onChange={workspace.setActivationCode}
                  placeholder="ACTV-1234-5678"
                />
                <ActionButton
                  onClick={() => void workspace.activateDesktopAccess()}
                  disabled={workspace.isBusy || !workspace.activationCode}
                >
                  Activate desktop access
                </ActionButton>
              </div>
            ) : workspace.supportsDeveloperSessionBootstrap ? (
              <div style={{ display: 'grid', gap: '12px' }}>
                <FormField
                  id="store-korsenex-token"
                  label="Korsenex token"
                  value={workspace.korsenexToken}
                  onChange={workspace.setKorsenexToken}
                  placeholder="stub:sub=cashier-1;email=cashier@acme.local;name=Counter Cashier"
                />
                <ActionButton
                  onClick={() => void workspace.startSession()}
                  disabled={workspace.isBusy || !workspace.korsenexToken}
                >
                  Start runtime session
                </ActionButton>
              </div>
            ) : (
              <p style={{ color: '#4e5871', marginBottom: 0 }}>{copy.body}</p>
            )}
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px', marginTop: '18px' }}>
            <ActionButton onClick={props.onResumeSelling} disabled={!ctaState.canResumeSelling}>
              Resume selling
            </ActionButton>
            {workspace.actor ? (
              <>
                <ActionButton onClick={() => void workspace.refreshRuntimeSession()} disabled={workspace.isBusy || !workspace.isSessionLive}>
                  Refresh runtime session
                </ActionButton>
                <ActionButton onClick={() => void workspace.signOut()} disabled={workspace.isBusy}>
                  Sign out
                </ActionButton>
              </>
            ) : null}
          </div>

          {workspace.errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{workspace.errorMessage}</p> : null}
        </SectionCard>

        <div style={{ display: 'grid', gap: '20px', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
          <SectionCard eyebrow="Attendance" title="Clock-in posture">
            <DetailList
              items={[
                {
                  label: 'Attendance',
                  value: workspace.activeAttendanceSession ? (
                    <StatusBadge label={workspace.activeAttendanceSession.status} tone="success" />
                  ) : (
                    <StatusBadge label="Not clocked in" tone="warning" />
                  ),
                },
                { label: 'Shift gate', value: ctaState.requiresShift ? 'Required' : 'Optional' },
                { label: 'Shift session', value: workspace.activeShiftSession?.shift_number ?? 'No active shift' },
                {
                  label: 'Register',
                  value: workspace.activeCashierSession ? (
                    <StatusBadge label={workspace.activeCashierSession.status} tone="success" />
                  ) : (
                    <StatusBadge label="Closed" tone="warning" />
                  ),
                },
                { label: 'Attendance gate', value: ctaState.requiresAttendance ? 'Required' : 'Optional' },
              ]}
            />
          </SectionCard>
          <SectionCard eyebrow="Runtime" title="Counter posture">
            <DetailList
              items={[
                { label: 'Device', value: ctaState.selectedRuntimeDevice?.device_name ?? 'No runtime device selected' },
                { label: 'Device code', value: ctaState.selectedRuntimeDevice?.device_code ?? 'Unknown' },
                { label: 'Assigned staff', value: ctaState.selectedRuntimeDevice?.assigned_staff_full_name ?? 'Not assigned' },
                { label: 'Opening float', value: workspace.cashierOpeningFloatAmount || 'Not entered' },
              ]}
            />
          </SectionCard>
        </div>

        <div style={{ display: 'grid', gap: '20px' }}>
          <div style={{ display: 'grid', gap: '20px', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))' }}>
            <StoreShiftSection workspace={workspace} />
            <StoreAttendanceSection workspace={workspace} />
          </div>
          <StoreCashierSessionSection workspace={workspace} />
        </div>
      </div>

      <div style={{ display: 'grid', gap: '24px', alignContent: 'start' }}>
        <StoreRuntimeReleaseSection />
      </div>
    </div>
  );
}
