import { startTransition, useState } from 'react';
import { ActionButton, DetailList, SectionCard } from '@store/ui';
import type {
  ControlPlaneBranchManagementDashboard,
  ControlPlaneBranchRecord,
} from '@store/types';
import { ownerControlPlaneClient } from './client';

type OwnerBranchPerformanceSectionProps = {
  accessToken: string;
  tenantId: string;
  branches: ControlPlaneBranchRecord[];
};

function formatNumber(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(2);
}

function sumRecommendationSpend(dashboard: ControlPlaneBranchManagementDashboard): number {
  return dashboard.recommendations.reduce((sum, record) => {
    if (record.recommendation_status !== 'ORDER_NOW') {
      return sum;
    }
    return sum + record.estimated_purchase_cost;
  }, 0);
}

function isAtRiskBranch(dashboard: ControlPlaneBranchManagementDashboard): boolean {
  return (
    dashboard.operations.low_stock_count > 0
    || dashboard.operations.overdue_supplier_invoice_count > 0
    || dashboard.operations.supplier_blocker_count > 0
    || dashboard.procurement.approved_pending_receipt_count > 0
  );
}

export function OwnerBranchPerformanceSection({
  accessToken,
  tenantId,
  branches,
}: OwnerBranchPerformanceSectionProps) {
  const [dashboards, setDashboards] = useState<ControlPlaneBranchManagementDashboard[]>([]);
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  async function loadBranchPerformance() {
    if (!accessToken || !tenantId || branches.length === 0) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const nextDashboards = await Promise.all(
        branches.map((branch) =>
          ownerControlPlaneClient.getBranchManagementDashboard(accessToken, tenantId, branch.branch_id),
        ),
      );
      startTransition(() => {
        setDashboards(nextDashboards);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load branch performance');
    } finally {
      setIsBusy(false);
    }
  }

  const sales7dTotal = dashboards.reduce((sum, dashboard) => sum + dashboard.trade.sales_7d_total, 0);
  const atRiskBranches = dashboards.filter(isAtRiskBranch).length;
  const immediateReorderSpend = dashboards.reduce((sum, dashboard) => sum + sumRecommendationSpend(dashboard), 0);

  return (
    <SectionCard eyebrow="Owner reporting" title="Branch performance">
      <ActionButton onClick={() => void loadBranchPerformance()} disabled={isBusy || !accessToken || !tenantId || branches.length === 0}>
        Load branch performance
      </ActionButton>

      {dashboards.length > 0 ? (
        <div style={{ marginTop: '16px' }}>
          <DetailList
            items={[
              { label: 'Sales 7 days', value: formatNumber(sales7dTotal) },
              { label: 'At-risk branches', value: String(atRiskBranches) },
              { label: 'Immediate reorder spend', value: formatNumber(immediateReorderSpend) },
            ]}
          />

          <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
            {dashboards.map((dashboard) => (
              <li key={dashboard.branch_id}>
                {dashboard.branch_name}
                {' :: sales '}
                {formatNumber(dashboard.trade.sales_7d_total)}
                {' :: reorder spend '}
                {formatNumber(sumRecommendationSpend(dashboard))}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
