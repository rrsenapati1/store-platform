import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

export function StoreAttendanceSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const selectedRuntimeDevice = workspace.runtimeDevices.find((device) => device.id === workspace.selectedRuntimeDeviceId)
    ?? workspace.runtimeDevices[0]
    ?? null;
  const activeAttendanceSession = workspace.activeAttendanceSession;
  const attendanceHistory = workspace.attendanceSessions.filter((session) => session.status !== 'OPEN');
  const requiresShift = workspace.branchRuntimePolicy?.require_shift_for_attendance ?? false;
  const shiftGateSatisfied = !requiresShift || Boolean(workspace.activeShiftSession);
  const canOpenAttendanceSession = Boolean(
    workspace.isSessionLive
      && selectedRuntimeDevice?.assigned_staff_profile_id,
  ) && shiftGateSatisfied;
  const attendanceIntro = selectedRuntimeDevice?.assigned_staff_profile_id
    ? requiresShift && !workspace.activeShiftSession
      ? 'Open a branch shift before clocking in on this runtime device.'
      : 'Clock in on this runtime device before opening a cashier session.'
    : 'Assign this runtime device to a staff profile before clocking in.';
  const shiftDescriptor = workspace.activeShiftSession?.shift_number ?? 'No active shift';

  return (
    <SectionCard eyebrow="Staff presence" title="Attendance">
      {activeAttendanceSession ? (
        <>
          <h3 style={{ marginBottom: '10px' }}>Active attendance session</h3>
          <DetailList
            items={[
              { label: 'Attendance number', value: activeAttendanceSession.attendance_number },
              {
                label: 'Status',
                value: <StatusBadge label={activeAttendanceSession.status} tone={activeAttendanceSession.status === 'OPEN' ? 'success' : 'warning'} />,
              },
              { label: 'Device', value: activeAttendanceSession.device_name ?? activeAttendanceSession.device_code ?? 'Unknown' },
              { label: 'Staff member', value: activeAttendanceSession.staff_full_name ?? 'Unknown' },
              { label: 'Opened at', value: activeAttendanceSession.opened_at },
              { label: 'Clock-in note', value: activeAttendanceSession.clock_in_note || 'None' },
              { label: 'Linked shift', value: activeAttendanceSession.shift_session_id ?? shiftDescriptor },
              { label: 'Linked cashier sessions', value: String(activeAttendanceSession.linked_cashier_sessions_count) },
            ]}
          />
          <div style={{ marginTop: '16px' }}>
            <FormField
              id="runtime-attendance-clock-out-note"
              label="Clock-out note"
              value={workspace.attendanceClockOutNote}
              onChange={workspace.setAttendanceClockOutNote}
            />
            <ActionButton onClick={() => void workspace.closeAttendanceSession()} disabled={workspace.isBusy || !workspace.isSessionLive}>
              Clock out
            </ActionButton>
          </div>
        </>
      ) : (
        <>
          <p style={{ marginTop: 0, color: '#4e5871' }}>
            {attendanceIntro}
          </p>
          <DetailList
            items={[
              { label: 'Selected device', value: selectedRuntimeDevice?.device_name ?? 'None' },
              { label: 'Device code', value: selectedRuntimeDevice?.device_code ?? 'None' },
              { label: 'Assigned staff member', value: selectedRuntimeDevice?.assigned_staff_full_name ?? 'Not assigned' },
              { label: 'Active shift', value: shiftDescriptor },
            ]}
          />
          <div style={{ marginTop: '16px' }}>
            <FormField
              id="runtime-attendance-clock-in-note"
              label="Clock-in note"
              value={workspace.attendanceClockInNote}
              onChange={workspace.setAttendanceClockInNote}
            />
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <ActionButton onClick={() => void workspace.openAttendanceSession()} disabled={workspace.isBusy || !canOpenAttendanceSession}>
                Clock in
              </ActionButton>
              <ActionButton
                onClick={() => void workspace.loadAttendanceSessions()}
                disabled={workspace.isBusy || !workspace.isSessionLive || !selectedRuntimeDevice?.assigned_staff_profile_id}
              >
                Refresh attendance
              </ActionButton>
            </div>
          </div>
        </>
      )}

      {attendanceHistory.length ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Attendance history</h3>
          <ul style={{ marginBottom: 0, color: '#4e5871', lineHeight: 1.7 }}>
            {attendanceHistory.map((session) => (
              <li key={session.id}>
                <span>
                  {session.attendance_number} :: {session.staff_full_name ?? 'Unknown'} :: {session.device_code ?? session.device_name ?? 'Unknown'} :: {session.status}
                </span>
                {session.clock_out_note ? (
                  <>
                    <span> :: </span>
                    <span>{session.clock_out_note}</span>
                  </>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </SectionCard>
  );
}
