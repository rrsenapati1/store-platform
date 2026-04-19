import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

export function StoreCashierSessionSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const selectedRuntimeDevice = workspace.runtimeDevices.find((device) => device.id === workspace.selectedRuntimeDeviceId)
    ?? workspace.runtimeDevices[0]
    ?? null;
  const activeCashierSession = workspace.activeCashierSession;
  const requiresAttendance = workspace.branchRuntimePolicy?.require_attendance_for_cashier ?? true;
  const attendanceGateSatisfied = !requiresAttendance || Boolean(workspace.activeAttendanceSession);
  const canOpenCashierSession = Boolean(
    workspace.isSessionLive
      && selectedRuntimeDevice?.assigned_staff_profile_id
      && workspace.cashierOpeningFloatAmount !== '',
  ) && attendanceGateSatisfied;
  const cashierIntro = selectedRuntimeDevice?.assigned_staff_profile_id
    ? requiresAttendance && !workspace.activeAttendanceSession
      ? 'Open an attendance session before opening a cashier session on this terminal.'
      : 'Open a cashier session before billing or processing returns on this terminal.'
    : 'Assign this runtime device to a staff profile before opening a cashier session.';

  return (
    <SectionCard eyebrow="Checkout authority" title="Cashier session">
      {activeCashierSession ? (
        <>
          <h3 style={{ marginBottom: '10px' }}>Active cashier session</h3>
          <DetailList
            items={[
              { label: 'Session number', value: activeCashierSession.session_number },
              {
                label: 'Status',
                value: <StatusBadge label={activeCashierSession.status} tone={activeCashierSession.status === 'OPEN' ? 'success' : 'warning'} />,
              },
              { label: 'Device', value: activeCashierSession.device_name ?? activeCashierSession.device_code ?? 'Unknown' },
              { label: 'Cashier', value: activeCashierSession.staff_full_name ?? 'Unknown' },
              { label: 'Opening float', value: String(activeCashierSession.opening_float_amount) },
              { label: 'Opened at', value: activeCashierSession.opened_at },
              { label: 'Opening note', value: activeCashierSession.opening_note || 'None' },
            ]}
          />
          <div style={{ marginTop: '16px' }}>
            <FormField
              id="runtime-cashier-closing-note"
              label="Closing note"
              value={workspace.cashierClosingNote}
              onChange={workspace.setCashierClosingNote}
            />
            <ActionButton onClick={() => void workspace.closeCashierSession()} disabled={workspace.isBusy || !workspace.isSessionLive}>
              Close cashier session
            </ActionButton>
          </div>
        </>
      ) : (
        <>
          <p style={{ marginTop: 0, color: '#4e5871' }}>
            {cashierIntro}
          </p>
          <DetailList
            items={[
              { label: 'Selected device', value: selectedRuntimeDevice?.device_name ?? 'None' },
              { label: 'Device code', value: selectedRuntimeDevice?.device_code ?? 'None' },
              { label: 'Assigned cashier', value: selectedRuntimeDevice?.assigned_staff_full_name ?? 'Not assigned' },
              {
                label: 'Attendance gate',
                value: <StatusBadge label={requiresAttendance ? 'REQUIRED' : 'OPTIONAL'} tone={requiresAttendance ? 'warning' : 'neutral'} />,
              },
            ]}
          />
          <div style={{ marginTop: '16px' }}>
            <FormField
              id="runtime-cashier-opening-float"
              label="Opening float amount"
              value={workspace.cashierOpeningFloatAmount}
              onChange={workspace.setCashierOpeningFloatAmount}
            />
            <FormField
              id="runtime-cashier-opening-note"
              label="Opening note"
              value={workspace.cashierOpeningNote}
              onChange={workspace.setCashierOpeningNote}
            />
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <ActionButton onClick={() => void workspace.openCashierSession()} disabled={workspace.isBusy || !canOpenCashierSession}>
                Open register
              </ActionButton>
              <ActionButton
                onClick={() => void workspace.loadCashierSessions()}
                disabled={workspace.isBusy || !workspace.isSessionLive || !selectedRuntimeDevice?.assigned_staff_profile_id}
              >
                Refresh cashier session
              </ActionButton>
            </div>
          </div>
        </>
      )}
    </SectionCard>
  );
}
