import { startTransition, useState } from 'react';
import { ActionButton, DetailList, SectionCard } from '@store/ui';
import type { ControlPlaneBranchManagementDashboard } from '@store/types';
import { storeControlPlaneClient } from './client';

type StoreBranchDecisionSupportSectionProps = {
  accessToken: string;
  tenantId: string;
  branchId: string;
};

function formatNumber(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(2);
}

function reorderQuantity(dashboard: ControlPlaneBranchManagementDashboard): number {
  return dashboard.recommendations.reduce((sum, record) => {
    if (record.recommendation_status !== 'ORDER_NOW') {
      return sum;
    }
    return sum + record.net_recommended_order_quantity;
  }, 0);
}

export function StoreBranchDecisionSupportSection({
  accessToken,
  tenantId,
  branchId,
}: StoreBranchDecisionSupportSectionProps) {
  const [dashboard, setDashboard] = useState<ControlPlaneBranchManagementDashboard | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  async function loadDecisionSupport() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const nextDashboard = await storeControlPlaneClient.getBranchManagementDashboard(accessToken, tenantId, branchId);
      startTransition(() => {
        setDashboard(nextDashboard);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load branch decision support');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <SectionCard eyebrow="Branch manager reporting" title="Decision support">
      <ActionButton onClick={() => void loadDecisionSupport()} disabled={isBusy || !accessToken || !tenantId || !branchId}>
        Load decision support
      </ActionButton>

      {dashboard ? (
        <div style={{ marginTop: '16px' }}>
          <DetailList
            items={[
              { label: 'Immediate reorder quantity', value: formatNumber(reorderQuantity(dashboard)) },
              { label: 'Approved pending receipt', value: String(dashboard.procurement.approved_pending_receipt_count) },
              { label: 'Outstanding payables', value: formatNumber(dashboard.procurement.outstanding_payables_total) },
            ]}
          />

          <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
            {dashboard.recommendations.map((record) => (
              <li key={record.product_id}>
                {record.product_name}
                {' :: reorder '}
                {formatNumber(record.net_recommended_order_quantity)}
                {' :: spend '}
                {formatNumber(record.estimated_purchase_cost)}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
