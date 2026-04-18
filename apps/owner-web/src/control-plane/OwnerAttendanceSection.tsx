import { startTransition, useMemo, useState } from 'react';
import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { ControlPlaneAttendanceSession } from '@store/types';
import { ownerControlPlaneClient } from './client';

type OwnerAttendanceSectionProps = {
  accessToken: string;
  tenantId: string;
  branchId: string;
};

function buildAttendanceTone(status: string) {
  if (status === 'OPEN') {
    return 'success';
  }
  if (status === 'FORCED_CLOSED') {
    return 'warning';
  }
  return 'neutral';
}

function summarizeAttendance(record: ControlPlaneAttendanceSession): string {
  return `${record.attendance_number} :: ${record.staff_full_name ?? 'Unknown cashier'} :: ${record.device_code ?? record.device_name ?? 'Unknown device'}`;
}

export function OwnerAttendanceSection({
  accessToken,
  tenantId,
  branchId,
}: OwnerAttendanceSectionProps) {
  const [attendanceSessions, setAttendanceSessions] = useState<ControlPlaneAttendanceSession[]>([]);
  const [selectedAttendanceSessionId, setSelectedAttendanceSessionId] = useState('');
  const [forceCloseReason, setForceCloseReason] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  const selectedSession = useMemo(
    () => attendanceSessions.find((session) => session.id === selectedAttendanceSessionId)
      ?? attendanceSessions.find((session) => session.status === 'OPEN')
      ?? attendanceSessions[0]
      ?? null,
    [attendanceSessions, selectedAttendanceSessionId],
  );
  const activeSessions = useMemo(
    () => attendanceSessions.filter((session) => session.status === 'OPEN'),
    [attendanceSessions],
  );
  const sessionHistory = useMemo(
    () => attendanceSessions.filter((session) => session.status !== 'OPEN'),
    [attendanceSessions],
  );

  async function loadAttendanceSessions() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const response = await ownerControlPlaneClient.listBranchAttendanceSessions(accessToken, tenantId, branchId);
      const nextSelectedId = response.records.some((session) => session.id === selectedAttendanceSessionId)
        ? selectedAttendanceSessionId
        : response.records.find((session) => session.status === 'OPEN')?.id ?? response.records[0]?.id ?? '';
      startTransition(() => {
        setAttendanceSessions(response.records);
        setSelectedAttendanceSessionId(nextSelectedId);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load attendance sessions.');
    } finally {
      setIsBusy(false);
    }
  }

  async function forceCloseSelectedAttendance() {
    if (!accessToken || !tenantId || !branchId || !selectedSession || selectedSession.status !== 'OPEN') {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const updated = await ownerControlPlaneClient.forceCloseBranchAttendanceSession(
        accessToken,
        tenantId,
        branchId,
        selectedSession.id,
        { reason: forceCloseReason },
      );
      startTransition(() => {
        setAttendanceSessions((current) => current.map((session) => (session.id === updated.id ? updated : session)));
        setSelectedAttendanceSessionId(updated.id);
        setForceCloseReason('');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to force-close attendance session.');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <SectionCard eyebrow="Staff presence governance" title="Attendance board">
      <ActionButton onClick={() => void loadAttendanceSessions()} disabled={isBusy || !accessToken || !tenantId || !branchId}>
        Refresh attendance sessions
      </ActionButton>

      {activeSessions.length ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Active attendance</h3>
          <ul style={{ marginBottom: 0, color: '#4e5871', lineHeight: 1.7 }}>
            {activeSessions.map((session) => (
              <li key={session.id}>
                <button
                  type="button"
                  onClick={() => setSelectedAttendanceSessionId(session.id)}
                  style={{ background: 'none', border: 0, color: '#25314f', cursor: 'pointer', fontWeight: 600, padding: 0 }}
                >
                  {summarizeAttendance(session)}
                </button>{' '}
                <StatusBadge label={session.status} tone={buildAttendanceTone(session.status)} />
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {sessionHistory.length ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Attendance history</h3>
          <ul style={{ marginBottom: 0, color: '#4e5871', lineHeight: 1.7 }}>
            {sessionHistory.map((session) => (
              <li key={session.id}>
                <button
                  type="button"
                  onClick={() => setSelectedAttendanceSessionId(session.id)}
                  style={{ background: 'none', border: 0, color: '#25314f', cursor: 'pointer', fontWeight: 600, padding: 0 }}
                >
                  {summarizeAttendance(session)}
                </button>{' '}
                <StatusBadge label={session.status} tone={buildAttendanceTone(session.status)} />
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {!attendanceSessions.length ? (
        <p style={{ color: '#4e5871', marginBottom: 0, marginTop: '16px' }}>
          Load attendance sessions to inspect active clock-ins and recent clock-outs.
        </p>
      ) : null}

      {selectedSession ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Selected attendance details</h3>
          <DetailList
            items={[
              { label: 'Attendance number', value: selectedSession.attendance_number },
              { label: 'Status', value: <StatusBadge label={selectedSession.status} tone={buildAttendanceTone(selectedSession.status)} /> },
              { label: 'Staff member', value: selectedSession.staff_full_name ?? 'Unknown' },
              { label: 'Device', value: selectedSession.device_name ?? selectedSession.device_code ?? 'Unknown' },
              { label: 'Clocked in at', value: selectedSession.opened_at },
              { label: 'Clocked out at', value: selectedSession.closed_at ?? 'Open' },
              { label: 'Clock-in note', value: selectedSession.clock_in_note ?? 'None' },
              { label: 'Clock-out note', value: selectedSession.clock_out_note ?? 'None' },
              { label: 'Linked cashier sessions', value: String(selectedSession.linked_cashier_sessions_count) },
              { label: 'Force-close reason', value: selectedSession.force_close_reason ?? 'None' },
            ]}
          />

          {selectedSession.status === 'OPEN' ? (
            <div style={{ marginTop: '16px' }}>
              <FormField
                id="owner-attendance-force-close-reason"
                label="Force-close reason"
                value={forceCloseReason}
                onChange={setForceCloseReason}
              />
              <ActionButton onClick={() => void forceCloseSelectedAttendance()} disabled={isBusy || !forceCloseReason.trim()}>
                Force-close selected attendance
              </ActionButton>
            </div>
          ) : null}
        </div>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
