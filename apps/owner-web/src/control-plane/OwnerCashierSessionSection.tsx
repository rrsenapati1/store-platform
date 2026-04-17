import { startTransition, useMemo, useState } from 'react';
import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { ControlPlaneCashierSession } from '@store/types';
import { ownerControlPlaneClient } from './client';

type OwnerCashierSessionSectionProps = {
  accessToken: string;
  tenantId: string;
  branchId: string;
};

function buildSessionTone(status: string) {
  if (status === 'OPEN') {
    return 'success';
  }
  if (status === 'FORCED_CLOSED') {
    return 'warning';
  }
  return 'neutral';
}

function summarizeSession(record: ControlPlaneCashierSession): string {
  return `${record.session_number} :: ${record.staff_full_name ?? 'Unknown cashier'} :: ${record.device_code ?? record.device_name ?? 'Unknown device'}`;
}

export function OwnerCashierSessionSection({
  accessToken,
  tenantId,
  branchId,
}: OwnerCashierSessionSectionProps) {
  const [cashierSessions, setCashierSessions] = useState<ControlPlaneCashierSession[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState('');
  const [forceCloseReason, setForceCloseReason] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  const selectedSession = useMemo(
    () => cashierSessions.find((session) => session.id === selectedSessionId)
      ?? cashierSessions.find((session) => session.status === 'OPEN')
      ?? cashierSessions[0]
      ?? null,
    [cashierSessions, selectedSessionId],
  );
  const activeSessions = useMemo(
    () => cashierSessions.filter((session) => session.status === 'OPEN'),
    [cashierSessions],
  );
  const sessionHistory = useMemo(
    () => cashierSessions.filter((session) => session.status !== 'OPEN'),
    [cashierSessions],
  );

  async function loadCashierSessions() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const response = await ownerControlPlaneClient.listBranchCashierSessions(accessToken, tenantId, branchId);
      const nextSelectedId = response.records.some((session) => session.id === selectedSessionId)
        ? selectedSessionId
        : response.records.find((session) => session.status === 'OPEN')?.id ?? response.records[0]?.id ?? '';
      startTransition(() => {
        setCashierSessions(response.records);
        setSelectedSessionId(nextSelectedId);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load cashier sessions.');
    } finally {
      setIsBusy(false);
    }
  }

  async function forceCloseSelectedSession() {
    if (!accessToken || !tenantId || !branchId || !selectedSession || selectedSession.status !== 'OPEN') {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const updated = await ownerControlPlaneClient.forceCloseBranchCashierSession(
        accessToken,
        tenantId,
        branchId,
        selectedSession.id,
        { reason: forceCloseReason },
      );
      startTransition(() => {
        setCashierSessions((current) => current.map((session) => (session.id === updated.id ? updated : session)));
        setSelectedSessionId(updated.id);
        setForceCloseReason('');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to force-close cashier session.');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <SectionCard eyebrow="Branch checkout governance" title="Cashier session board">
      <ActionButton onClick={() => void loadCashierSessions()} disabled={isBusy || !accessToken || !tenantId || !branchId}>
        Refresh cashier sessions
      </ActionButton>

      {activeSessions.length ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Active sessions</h3>
          <ul style={{ marginBottom: 0, color: '#4e5871', lineHeight: 1.7 }}>
            {activeSessions.map((session) => (
              <li key={session.id}>
                <button
                  type="button"
                  onClick={() => setSelectedSessionId(session.id)}
                  style={{ background: 'none', border: 0, color: '#25314f', cursor: 'pointer', fontWeight: 600, padding: 0 }}
                >
                  {summarizeSession(session)}
                </button>{' '}
                <StatusBadge label={session.status} tone={buildSessionTone(session.status)} />
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {sessionHistory.length ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Session history</h3>
          <ul style={{ marginBottom: 0, color: '#4e5871', lineHeight: 1.7 }}>
            {sessionHistory.map((session) => (
              <li key={session.id}>
                <button
                  type="button"
                  onClick={() => setSelectedSessionId(session.id)}
                  style={{ background: 'none', border: 0, color: '#25314f', cursor: 'pointer', fontWeight: 600, padding: 0 }}
                >
                  {summarizeSession(session)}
                </button>{' '}
                <StatusBadge label={session.status} tone={buildSessionTone(session.status)} />
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {!cashierSessions.length ? (
        <p style={{ color: '#4e5871', marginBottom: 0, marginTop: '16px' }}>
          Load cashier sessions to inspect active terminals and recent closed sessions.
        </p>
      ) : null}

      {selectedSession ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Selected session details</h3>
          <DetailList
            items={[
              { label: 'Session number', value: selectedSession.session_number },
              { label: 'Status', value: <StatusBadge label={selectedSession.status} tone={buildSessionTone(selectedSession.status)} /> },
              { label: 'Cashier', value: selectedSession.staff_full_name ?? 'Unknown' },
              { label: 'Device', value: selectedSession.device_name ?? selectedSession.device_code ?? 'Unknown' },
              { label: 'Opening float', value: String(selectedSession.opening_float_amount) },
              { label: 'Opened at', value: selectedSession.opened_at },
              { label: 'Closed at', value: selectedSession.closed_at ?? 'Open' },
              { label: 'Gross billed amount', value: String(selectedSession.gross_billed_amount) },
              { label: 'Linked sales', value: String(selectedSession.linked_sales_count) },
              { label: 'Linked returns', value: String(selectedSession.linked_returns_count) },
              { label: 'Opening note', value: selectedSession.opening_note ?? 'None' },
              { label: 'Closing note', value: selectedSession.closing_note ?? 'None' },
              { label: 'Force-close reason', value: selectedSession.force_close_reason ?? 'None' },
            ]}
          />

          {selectedSession.status === 'OPEN' ? (
            <div style={{ marginTop: '16px' }}>
              <FormField
                id="owner-cashier-session-force-close-reason"
                label="Force-close reason"
                value={forceCloseReason}
                onChange={setForceCloseReason}
              />
              <ActionButton onClick={() => void forceCloseSelectedSession()} disabled={isBusy || !forceCloseReason.trim()}>
                Force-close selected session
              </ActionButton>
            </div>
          ) : null}
        </div>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
