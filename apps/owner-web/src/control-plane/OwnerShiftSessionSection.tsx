import { startTransition, useMemo, useState } from 'react';
import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { ControlPlaneShiftSession } from '@store/types';
import { ownerControlPlaneClient } from './client';

type OwnerShiftSessionSectionProps = {
  accessToken: string;
  tenantId: string;
  branchId: string;
};

function buildShiftTone(status: string) {
  if (status === 'OPEN') {
    return 'success';
  }
  if (status === 'FORCED_CLOSED') {
    return 'warning';
  }
  return 'neutral';
}

function summarizeShift(record: ControlPlaneShiftSession): string {
  return `${record.shift_number} :: ${record.shift_name} :: attendance ${record.linked_attendance_sessions_count} :: cashier ${record.linked_cashier_sessions_count}`;
}

export function OwnerShiftSessionSection({
  accessToken,
  tenantId,
  branchId,
}: OwnerShiftSessionSectionProps) {
  const [shiftSessions, setShiftSessions] = useState<ControlPlaneShiftSession[]>([]);
  const [selectedShiftSessionId, setSelectedShiftSessionId] = useState('');
  const [forceCloseReason, setForceCloseReason] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  const selectedSession = useMemo(
    () => shiftSessions.find((session) => session.id === selectedShiftSessionId)
      ?? shiftSessions.find((session) => session.status === 'OPEN')
      ?? shiftSessions[0]
      ?? null,
    [selectedShiftSessionId, shiftSessions],
  );
  const activeSessions = useMemo(
    () => shiftSessions.filter((session) => session.status === 'OPEN'),
    [shiftSessions],
  );
  const sessionHistory = useMemo(
    () => shiftSessions.filter((session) => session.status !== 'OPEN'),
    [shiftSessions],
  );

  async function loadShiftSessions() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const response = await ownerControlPlaneClient.listBranchShiftSessions(accessToken, tenantId, branchId);
      const nextSelectedId = response.records.some((session) => session.id === selectedShiftSessionId)
        ? selectedShiftSessionId
        : response.records.find((session) => session.status === 'OPEN')?.id ?? response.records[0]?.id ?? '';
      startTransition(() => {
        setShiftSessions(response.records);
        setSelectedShiftSessionId(nextSelectedId);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load shift sessions.');
    } finally {
      setIsBusy(false);
    }
  }

  async function forceCloseSelectedShiftSession() {
    if (!accessToken || !tenantId || !branchId || !selectedSession || selectedSession.status !== 'OPEN') {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const updated = await ownerControlPlaneClient.forceCloseBranchShiftSession(
        accessToken,
        tenantId,
        branchId,
        selectedSession.id,
        { reason: forceCloseReason },
      );
      startTransition(() => {
        setShiftSessions((current) => current.map((session) => (session.id === updated.id ? updated : session)));
        setSelectedShiftSessionId(updated.id);
        setForceCloseReason('');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to force-close shift session.');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <SectionCard eyebrow="Branch shift governance" title="Shift board">
      <ActionButton onClick={() => void loadShiftSessions()} disabled={isBusy || !accessToken || !tenantId || !branchId}>
        Refresh shift sessions
      </ActionButton>

      {activeSessions.length ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Active shifts</h3>
          <ul style={{ marginBottom: 0, color: '#4e5871', lineHeight: 1.7 }}>
            {activeSessions.map((session) => (
              <li key={session.id}>
                <button
                  type="button"
                  onClick={() => setSelectedShiftSessionId(session.id)}
                  style={{ background: 'none', border: 0, color: '#25314f', cursor: 'pointer', fontWeight: 600, padding: 0 }}
                >
                  {summarizeShift(session)}
                </button>{' '}
                <StatusBadge label={session.status} tone={buildShiftTone(session.status)} />
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {sessionHistory.length ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Shift history</h3>
          <ul style={{ marginBottom: 0, color: '#4e5871', lineHeight: 1.7 }}>
            {sessionHistory.map((session) => (
              <li key={session.id}>
                <button
                  type="button"
                  onClick={() => setSelectedShiftSessionId(session.id)}
                  style={{ background: 'none', border: 0, color: '#25314f', cursor: 'pointer', fontWeight: 600, padding: 0 }}
                >
                  {summarizeShift(session)}
                </button>{' '}
                <StatusBadge label={session.status} tone={buildShiftTone(session.status)} />
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {!shiftSessions.length ? (
        <p style={{ color: '#4e5871', marginBottom: 0, marginTop: '16px' }}>
          Load shift sessions to inspect current branch coverage and recent closures.
        </p>
      ) : null}

      {selectedSession ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Selected shift details</h3>
          <DetailList
            items={[
              { label: 'Shift number', value: selectedSession.shift_number },
              { label: 'Status', value: <StatusBadge label={selectedSession.status} tone={buildShiftTone(selectedSession.status)} /> },
              { label: 'Shift name', value: selectedSession.shift_name },
              { label: 'Opened at', value: selectedSession.opened_at },
              { label: 'Closed at', value: selectedSession.closed_at ?? 'Open' },
              { label: 'Opening note', value: selectedSession.opening_note ?? 'None' },
              { label: 'Closing note', value: selectedSession.closing_note ?? 'None' },
              { label: 'Linked attendance sessions', value: String(selectedSession.linked_attendance_sessions_count) },
              { label: 'Linked cashier sessions', value: String(selectedSession.linked_cashier_sessions_count) },
              { label: 'Force-close reason', value: selectedSession.force_close_reason ?? 'None' },
            ]}
          />

          {selectedSession.status === 'OPEN' ? (
            <div style={{ marginTop: '16px' }}>
              <FormField
                id="owner-shift-session-force-close-reason"
                label="Force-close reason"
                value={forceCloseReason}
                onChange={setForceCloseReason}
              />
              <ActionButton onClick={() => void forceCloseSelectedShiftSession()} disabled={isBusy || !forceCloseReason.trim()}>
                Force-close selected shift
              </ActionButton>
            </div>
          ) : null}
        </div>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
