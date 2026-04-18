import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function buildShiftTone(status: string): 'neutral' | 'success' | 'warning' {
  if (status === 'OPEN') {
    return 'success';
  }
  if (status === 'FORCED_CLOSED') {
    return 'warning';
  }
  return 'neutral';
}

export function StoreShiftSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const activeShiftSession = workspace.activeShiftSession;
  const shiftHistory = workspace.shiftSessions.filter((session) => session.status !== 'OPEN');
  const branchRuntimePolicy = workspace.branchRuntimePolicy;
  const canOpenShiftSession = Boolean(workspace.isSessionLive && !activeShiftSession && workspace.shiftName.trim());

  return (
    <SectionCard eyebrow="Branch shift governance" title="Shift session">
      <DetailList
        items={[
          {
            label: 'Shift required before attendance',
            value: (
              <StatusBadge
                label={branchRuntimePolicy?.require_shift_for_attendance ? 'REQUIRED' : 'OPTIONAL'}
                tone={branchRuntimePolicy?.require_shift_for_attendance ? 'warning' : 'neutral'}
              />
            ),
          },
          {
            label: 'Offline sales',
            value: (
              <StatusBadge
                label={branchRuntimePolicy?.allow_offline_sales === false ? 'BLOCKED' : 'ALLOWED'}
                tone={branchRuntimePolicy?.allow_offline_sales === false ? 'warning' : 'success'}
              />
            ),
          },
          {
            label: 'Pending offline limit',
            value: String(branchRuntimePolicy?.max_pending_offline_sales ?? 25),
          },
        ]}
      />

      {activeShiftSession ? (
        <>
          <h3 style={{ marginBottom: '10px', marginTop: '16px' }}>Active shift session</h3>
          <DetailList
            items={[
              { label: 'Shift number', value: activeShiftSession.shift_number },
              {
                label: 'Status',
                value: <StatusBadge label={activeShiftSession.status} tone={buildShiftTone(activeShiftSession.status)} />,
              },
              { label: 'Shift name', value: activeShiftSession.shift_name },
              { label: 'Opened at', value: activeShiftSession.opened_at },
              { label: 'Opening note', value: activeShiftSession.opening_note || 'None' },
              { label: 'Linked attendance sessions', value: String(activeShiftSession.linked_attendance_sessions_count) },
              { label: 'Linked cashier sessions', value: String(activeShiftSession.linked_cashier_sessions_count) },
            ]}
          />
          <div style={{ marginTop: '16px' }}>
            <FormField
              id="runtime-shift-closing-note"
              label="Shift closing note"
              value={workspace.shiftClosingNote}
              onChange={workspace.setShiftClosingNote}
            />
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <ActionButton onClick={() => void workspace.closeShiftSession()} disabled={workspace.isBusy || !workspace.isSessionLive}>
                Close shift session
              </ActionButton>
              <ActionButton onClick={() => void workspace.loadShiftSessions()} disabled={workspace.isBusy || !workspace.isSessionLive}>
                Refresh shift board
              </ActionButton>
            </div>
          </div>
        </>
      ) : (
        <>
          <p style={{ marginTop: '16px', color: '#4e5871' }}>
            Open a branch shift before attendance when shift governance is enabled for this branch.
          </p>
          <FormField
            id="runtime-shift-name"
            label="Shift name"
            value={workspace.shiftName}
            onChange={workspace.setShiftName}
            placeholder="Morning counter shift"
          />
          <FormField
            id="runtime-shift-opening-note"
            label="Shift opening note"
            value={workspace.shiftOpeningNote}
            onChange={workspace.setShiftOpeningNote}
            placeholder="Cash drawer counted and ready"
          />
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <ActionButton onClick={() => void workspace.openShiftSession()} disabled={workspace.isBusy || !canOpenShiftSession}>
              Open shift session
            </ActionButton>
            <ActionButton onClick={() => void workspace.loadShiftSessions()} disabled={workspace.isBusy || !workspace.isSessionLive}>
              Refresh shift board
            </ActionButton>
          </div>
        </>
      )}

      {shiftHistory.length ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Recent shift history</h3>
          <ul style={{ color: '#4e5871', lineHeight: 1.7, marginBottom: 0 }}>
            {shiftHistory.map((session) => (
              <li key={session.id}>
                {session.shift_number}
                {' :: '}
                {session.shift_name}
                {' :: '}
                {session.status}
                {session.force_close_reason ? ` :: ${session.force_close_reason}` : ''}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </SectionCard>
  );
}
