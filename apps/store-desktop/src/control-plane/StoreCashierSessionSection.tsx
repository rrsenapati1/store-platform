import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

export function StoreCashierSessionSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const selectedRuntimeDevice = workspace.runtimeDevices.find((device) => device.id === workspace.selectedRuntimeDeviceId)
    ?? workspace.runtimeDevices[0]
    ?? null;
  const activeCashierSession = workspace.activeCashierSession;
  const canOpenCashierSession = Boolean(
    workspace.isSessionLive
      && selectedRuntimeDevice?.assigned_staff_profile_id
      && workspace.cashierOpeningFloatAmount !== '',
  );

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
            {selectedRuntimeDevice?.assigned_staff_profile_id
              ? 'Open a cashier session before billing or processing returns on this terminal.'
              : 'Assign this runtime device to a staff profile before opening a cashier session.'}
          </p>
          <DetailList
            items={[
              { label: 'Selected device', value: selectedRuntimeDevice?.device_name ?? 'None' },
              { label: 'Device code', value: selectedRuntimeDevice?.device_code ?? 'None' },
              { label: 'Assigned cashier', value: selectedRuntimeDevice?.assigned_staff_full_name ?? 'Not assigned' },
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
                Open cashier session
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
