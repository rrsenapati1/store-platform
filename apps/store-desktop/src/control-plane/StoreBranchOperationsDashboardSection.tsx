import { useState } from 'react';
import { ActionButton, DetailList, SectionCard, StatusBadge } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';
import {
  runLoadBranchOperationsDashboard,
  type StoreBranchOperationsDashboardSnapshot,
} from './storeBranchOperationsDashboardActions';

function currentBusinessDate(): string {
  return new Date().toISOString().slice(0, 10);
}

function statusTone(value: boolean): 'success' | 'warning' {
  return value ? 'success' : 'warning';
}

function onlineTone(status: string | null | undefined): 'success' | 'warning' | 'neutral' {
  if ((status ?? '').toLowerCase() === 'online') {
    return 'success';
  }
  if (!status) {
    return 'neutral';
  }
  return 'warning';
}

export function StoreBranchOperationsDashboardSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const [snapshot, setSnapshot] = useState<StoreBranchOperationsDashboardSnapshot | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);
  const todayKey = currentBusinessDate();
  const todaysSales = workspace.sales.filter((record) => record.issued_on === todayKey);
  const todaysSalesTotal = todaysSales.reduce((sum, record) => sum + record.grand_total, 0);
  const latestSale = workspace.sales[0] ?? null;
  const openAttendanceCount = workspace.attendanceSessions.filter((record) => record.status === 'OPEN').length;
  const openCashierCount = workspace.cashierSessions.filter((record) => record.status === 'OPEN').length;
  const canRefresh = Boolean(workspace.accessToken && workspace.tenantId && workspace.branchId && workspace.isSessionLive);

  async function refreshDashboard() {
    if (!canRefresh) {
      return;
    }
    await runLoadBranchOperationsDashboard({
      accessToken: workspace.accessToken,
      tenantId: workspace.tenantId,
      branchId: workspace.branchId,
      setIsBusy,
      setErrorMessage,
      setSnapshot,
    });
  }

  return (
    <SectionCard eyebrow="Branch manager reporting" title="Branch operations dashboard">
      <p style={{ margin: 0, color: '#4e5871' }}>
        Read-only runtime dashboard for branch managers using the live branch session.
      </p>

      <div style={{ marginTop: '16px' }}>
        <h3 style={{ marginBottom: '10px', marginTop: 0 }}>Branch trade posture</h3>
        <DetailList
          items={[
            { label: 'Today sales', value: String(todaysSalesTotal) },
            { label: 'Invoices today', value: String(todaysSales.length) },
            { label: 'Latest invoice', value: latestSale ? `Invoice ${latestSale.invoice_number}` : 'No sales yet' },
          ]}
        />
      </div>

      <div style={{ marginTop: '16px' }}>
        <h3 style={{ marginBottom: '10px', marginTop: 0 }}>Workforce and session posture</h3>
        <DetailList
          items={[
            { label: 'Active shift', value: workspace.activeShiftSession?.shift_name ?? 'No active shift' },
            { label: 'Open attendance sessions', value: String(openAttendanceCount) },
            { label: 'Open cashier sessions', value: String(openCashierCount) },
            {
              label: 'Attendance required for cashier',
              value: (
                <StatusBadge
                  label={workspace.branchRuntimePolicy?.require_attendance_for_cashier ? 'REQUIRED' : 'OPTIONAL'}
                  tone={workspace.branchRuntimePolicy?.require_attendance_for_cashier ? 'warning' : 'neutral'}
                />
              ),
            },
            {
              label: 'Shift required for attendance',
              value: (
                <StatusBadge
                  label={workspace.branchRuntimePolicy?.require_shift_for_attendance ? 'REQUIRED' : 'OPTIONAL'}
                  tone={workspace.branchRuntimePolicy?.require_shift_for_attendance ? 'warning' : 'neutral'}
                />
              ),
            },
          ]}
        />
      </div>

      <div style={{ marginTop: '16px' }}>
        <h3 style={{ marginBottom: '10px', marginTop: 0 }}>Runtime and offline health</h3>
        <DetailList
          items={[
            {
              label: 'Runtime heartbeat',
              value: (
                <StatusBadge
                  label={workspace.runtimeHeartbeat?.status ?? 'UNKNOWN'}
                  tone={onlineTone(workspace.runtimeHeartbeat?.status)}
                />
              ),
            },
            { label: 'Pending offline sales', value: String(workspace.pendingOfflineSaleCount) },
            { label: 'Pending runtime mutations', value: String(workspace.pendingMutationCount) },
            { label: 'Offline conflicts', value: String(workspace.offlineConflictCount) },
            {
              label: 'Offline continuity',
              value: (
                <StatusBadge
                  label={workspace.offlineContinuityReady ? 'READY' : 'DEGRADED'}
                  tone={statusTone(workspace.offlineContinuityReady)}
                />
              ),
            },
            {
              label: 'Offline message',
              value: workspace.offlineContinuityMessage ? `Status: ${workspace.offlineContinuityMessage}` : 'No message',
            },
            { label: 'Runtime binding', value: workspace.runtimeBindingStatus ?? 'UNKNOWN' },
            { label: 'Hub service state', value: workspace.runtimeHubServiceState ?? 'UNKNOWN' },
          ]}
        />
      </div>

      <div style={{ marginTop: '16px' }}>
        <ActionButton onClick={() => void refreshDashboard()} disabled={isBusy || !canRefresh}>
          Refresh dashboard
        </ActionButton>
      </div>

      {snapshot ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px', marginTop: 0 }}>Stock-operation exceptions</h3>
          <DetailList
            items={[
              { label: 'Low-stock products', value: String(snapshot.replenishmentBoard.low_stock_count) },
              { label: 'Restock open', value: String(snapshot.restockBoard.open_count) },
              { label: 'Receiving ready', value: String(snapshot.receivingBoard.ready_count) },
              { label: 'Receiving variance', value: String(snapshot.receivingBoard.received_with_variance_count ?? 0) },
              { label: 'Count sessions open', value: String(snapshot.stockCountBoard.open_count) },
              { label: 'Expiring soon lots', value: String(snapshot.batchExpiryReport.expiring_soon_count) },
            ]}
          />

          <ul style={{ marginBottom: '16px', marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
            {snapshot.replenishmentBoard.records.slice(0, 3).map((record) => (
              <li key={record.product_id}>
                {record.product_name}
                {' :: '}
                {record.replenishment_status}
              </li>
            ))}
          </ul>

          <ul style={{ marginBottom: '16px', marginTop: 0, color: '#4e5871', lineHeight: 1.7 }}>
            {snapshot.receivingBoard.records.slice(0, 3).map((record) => (
              <li key={record.purchase_order_id}>
                {record.supplier_name}
                {' :: '}
                {record.purchase_order_number}
                {' :: '}
                {record.receiving_status}
              </li>
            ))}
          </ul>

          <ul style={{ marginBottom: 0, marginTop: 0, color: '#4e5871', lineHeight: 1.7 }}>
            {snapshot.batchExpiryReport.records.slice(0, 3).map((record) => (
              <li key={record.batch_lot_id}>
                {record.product_name}
                {' :: '}
                {record.batch_number}
                {' :: '}
                {record.status}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
