import { startTransition, useState } from 'react';
import { ActionButton, DetailList, SectionCard } from '@store/ui';
import type { ControlPlaneBranchCustomerReport, ControlPlaneCustomerDirectoryRecord } from '@store/types';
import { storeControlPlaneClient } from './client';

type StoreCustomerInsightsSectionProps = {
  accessToken: string;
  tenantId: string;
  branchId: string;
};

export function StoreCustomerInsightsSection({ accessToken, tenantId, branchId }: StoreCustomerInsightsSectionProps) {
  const [directory, setDirectory] = useState<ControlPlaneCustomerDirectoryRecord[]>([]);
  const [branchReport, setBranchReport] = useState<ControlPlaneBranchCustomerReport | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  async function loadCustomerInsights() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const [directoryResponse, reportResponse] = await Promise.all([
        storeControlPlaneClient.listCustomers(accessToken, tenantId),
        storeControlPlaneClient.getBranchCustomerReport(accessToken, tenantId, branchId),
      ]);
      startTransition(() => {
        setDirectory(directoryResponse.records);
        setBranchReport(reportResponse);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load customer insights');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <SectionCard eyebrow="Customer reporting" title="Customer insights">
      <ActionButton onClick={() => void loadCustomerInsights()} disabled={isBusy || !accessToken || !tenantId || !branchId}>
        Load customer insights
      </ActionButton>

      {branchReport ? (
        <div style={{ marginTop: '16px' }}>
          <DetailList
            items={[
              { label: 'Customers', value: String(branchReport.customer_count) },
              { label: 'Repeat customers', value: String(branchReport.repeat_customer_count) },
              { label: 'Anonymous sales', value: String(branchReport.anonymous_sales_count) },
              { label: 'Anonymous total', value: String(branchReport.anonymous_sales_total) },
            ]}
          />
        </div>
      ) : null}

      {directory.length ? (
        <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {directory.map((record) => (
            <li key={record.customer_id}>
              {record.name} {record.gstin ? `(${record.gstin})` : ''} - visits {record.visit_count} - lifetime {record.lifetime_value}
            </li>
          ))}
        </ul>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
