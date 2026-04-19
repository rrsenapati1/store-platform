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
          <p style={{ marginTop: 0, color: '#4e5871' }}>
            Start the runtime, clock in, open the register, and resume the active counter.
          </p>
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
              <p style={{ color: '#4e5871', marginBottom: 0 }}>
                Browser preview does not support production sign-in. Use the packaged desktop activation flow for operator access.
              </p>
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
