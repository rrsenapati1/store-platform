import { startTransition, useState } from 'react';
import { ActionButton, DetailList, SectionCard } from '@store/ui';
import type {
  ControlPlaneSupplierAgingReport,
  ControlPlaneSupplierDueScheduleReport,
  ControlPlaneSupplierEscalationReport,
  ControlPlaneSupplierExceptionReport,
  ControlPlaneSupplierPaymentActivityReport,
  ControlPlaneSupplierPayablesReport,
  ControlPlaneSupplierPerformanceReport,
  ControlPlaneSupplierSettlementBlockerReport,
  ControlPlaneSupplierSettlementReport,
  ControlPlaneSupplierStatementReport,
  ControlPlaneVendorDisputeBoard,
} from '@store/types';
import { ownerControlPlaneClient } from './client';

type OwnerSupplierReportingSectionProps = {
  accessToken: string;
  tenantId: string;
  branchId: string;
};

type SupplierReportingSnapshot = {
  payables: ControlPlaneSupplierPayablesReport;
  aging: ControlPlaneSupplierAgingReport;
  statements: ControlPlaneSupplierStatementReport;
  dueSchedule: ControlPlaneSupplierDueScheduleReport;
  disputes: ControlPlaneVendorDisputeBoard;
  exceptions: ControlPlaneSupplierExceptionReport;
  settlement: ControlPlaneSupplierSettlementReport;
  blockers: ControlPlaneSupplierSettlementBlockerReport;
  escalations: ControlPlaneSupplierEscalationReport;
  performance: ControlPlaneSupplierPerformanceReport;
  paymentActivity: ControlPlaneSupplierPaymentActivityReport;
};

function snapshotHealth(snapshot: SupplierReportingSnapshot): { label: string; staleCount: number } {
  const statuses = Object.values(snapshot).map((report) => report.snapshot_status ?? 'CURRENT');
  const staleCount = statuses.filter((status) => status === 'STALE_REFRESH_QUEUED').length;
  return {
    label: staleCount > 0 ? `${staleCount} refresh queued` : 'Current',
    staleCount,
  };
}

export function OwnerSupplierReportingSection({ accessToken, tenantId, branchId }: OwnerSupplierReportingSectionProps) {
  const [snapshot, setSnapshot] = useState<SupplierReportingSnapshot | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);
  const health = snapshot ? snapshotHealth(snapshot) : null;

  async function loadSupplierReporting() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const [
        payables,
        aging,
        statements,
        dueSchedule,
        disputes,
        exceptions,
        settlement,
        blockers,
        escalations,
        performance,
        paymentActivity,
      ] = await Promise.all([
        ownerControlPlaneClient.getSupplierPayablesReport(accessToken, tenantId, branchId),
        ownerControlPlaneClient.getSupplierAgingReport(accessToken, tenantId, branchId),
        ownerControlPlaneClient.getSupplierStatements(accessToken, tenantId, branchId),
        ownerControlPlaneClient.getSupplierDueSchedule(accessToken, tenantId, branchId),
        ownerControlPlaneClient.getVendorDisputeBoard(accessToken, tenantId, branchId),
        ownerControlPlaneClient.getSupplierExceptionReport(accessToken, tenantId, branchId),
        ownerControlPlaneClient.getSupplierSettlementReport(accessToken, tenantId, branchId),
        ownerControlPlaneClient.getSupplierSettlementBlockers(accessToken, tenantId, branchId),
        ownerControlPlaneClient.getSupplierEscalationReport(accessToken, tenantId, branchId),
        ownerControlPlaneClient.getSupplierPerformanceReport(accessToken, tenantId, branchId),
        ownerControlPlaneClient.getSupplierPaymentActivity(accessToken, tenantId, branchId),
      ]);
      startTransition(() => {
        setSnapshot({
          payables,
          aging,
          statements,
          dueSchedule,
          disputes,
          exceptions,
          settlement,
          blockers,
          escalations,
          performance,
          paymentActivity,
        });
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load supplier reporting');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <SectionCard eyebrow="Supplier reporting" title="Supplier reporting">
      <ActionButton onClick={() => void loadSupplierReporting()} disabled={isBusy || !accessToken || !tenantId || !branchId}>
        Load supplier reporting
      </ActionButton>

      {snapshot ? (
        <div style={{ marginTop: '16px' }}>
          <DetailList
            items={[
              { label: 'Snapshot health', value: health?.label ?? 'Current' },
              { label: 'Outstanding payables', value: String(snapshot.payables.outstanding_total) },
              { label: 'Open invoices', value: String(snapshot.aging.open_invoice_count) },
              { label: 'Suppliers on statement', value: String(snapshot.statements.supplier_count) },
              { label: 'Overdue invoices', value: String(snapshot.dueSchedule.overdue_invoice_count) },
              { label: 'Open disputes', value: String(snapshot.disputes.open_count) },
              { label: 'Suppliers with overdue disputes', value: String(snapshot.exceptions.suppliers_with_overdue_disputes) },
              { label: 'Hard blockers', value: String(snapshot.blockers.hard_hold_count) },
              { label: 'Finance escalations', value: String(snapshot.escalations.finance_escalation_count) },
              { label: 'At-risk suppliers', value: String(snapshot.performance.at_risk_count) },
              { label: 'Recent paid total', value: String(snapshot.paymentActivity.recent_30_days_paid_total) },
            ]}
          />

          {health && health.staleCount > 0 ? (
            <p style={{ color: '#4e5871', marginBottom: '16px', marginTop: '12px' }}>
              Some supplier snapshots are serving stale data while the worker refreshes them.
            </p>
          ) : null}

          <ul style={{ marginBottom: '16px', marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
            {snapshot.payables.records.slice(0, 3).map((record, index) => (
              <li key={`${record.purchase_invoice_number}-${index}`}>
                {record.supplier_name} :: {record.purchase_invoice_number} :: {record.outstanding_total}
              </li>
            ))}
          </ul>

          <ul style={{ marginBottom: '16px', marginTop: 0, color: '#4e5871', lineHeight: 1.7 }}>
            {snapshot.blockers.records.slice(0, 3).map((record) => (
              <li key={record.supplier_id}>
                {record.supplier_name} :: {record.hold_status} :: {record.outstanding_total}
              </li>
            ))}
          </ul>

          <ul style={{ marginBottom: 0, marginTop: 0, color: '#4e5871', lineHeight: 1.7 }}>
            {snapshot.escalations.records.slice(0, 3).map((record) => (
              <li key={record.dispute_id}>
                {record.supplier_name} :: {record.escalation_status}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
