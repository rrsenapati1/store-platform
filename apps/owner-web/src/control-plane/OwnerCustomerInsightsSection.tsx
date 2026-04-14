import { startTransition, useState } from 'react';
import { ActionButton, DetailList, FormField, SectionCard } from '@store/ui';
import type { ControlPlaneBranchCustomerReport, ControlPlaneCustomerDirectoryRecord, ControlPlaneCustomerHistoryResponse } from '@store/types';
import { ownerControlPlaneClient } from './client';

type OwnerCustomerInsightsSectionProps = {
  accessToken: string;
  tenantId: string;
  branchId: string;
};

export function OwnerCustomerInsightsSection({ accessToken, tenantId, branchId }: OwnerCustomerInsightsSectionProps) {
  const [directory, setDirectory] = useState<ControlPlaneCustomerDirectoryRecord[]>([]);
  const [branchReport, setBranchReport] = useState<ControlPlaneBranchCustomerReport | null>(null);
  const [selectedCustomerId, setSelectedCustomerId] = useState('');
  const [customerHistory, setCustomerHistory] = useState<ControlPlaneCustomerHistoryResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  async function loadCustomerInsights() {
    if (!accessToken || !tenantId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const [directoryResponse, reportResponse] = await Promise.all([
        ownerControlPlaneClient.listCustomers(accessToken, tenantId),
        branchId ? ownerControlPlaneClient.getBranchCustomerReport(accessToken, tenantId, branchId) : Promise.resolve(null),
      ]);
      const nextCustomerId = directoryResponse.records[0]?.customer_id ?? '';
      const history = nextCustomerId ? await ownerControlPlaneClient.getCustomerHistory(accessToken, tenantId, nextCustomerId) : null;
      startTransition(() => {
        setDirectory(directoryResponse.records);
        setBranchReport(reportResponse);
        setSelectedCustomerId(nextCustomerId);
        setCustomerHistory(history);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load customer insights');
    } finally {
      setIsBusy(false);
    }
  }

  async function loadSelectedCustomerHistory() {
    if (!accessToken || !tenantId || !selectedCustomerId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const history = await ownerControlPlaneClient.getCustomerHistory(accessToken, tenantId, selectedCustomerId);
      startTransition(() => {
        setCustomerHistory(history);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load customer history');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <SectionCard eyebrow="Customer reporting" title="Customer insights">
      <ActionButton onClick={() => void loadCustomerInsights()} disabled={isBusy || !accessToken || !tenantId}>
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
        <ul style={{ marginBottom: '16px', marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {directory.map((record) => (
            <li key={record.customer_id}>
              {record.name} {record.gstin ? `(${record.gstin})` : ''} - visits {record.visit_count} - lifetime {record.lifetime_value}
            </li>
          ))}
        </ul>
      ) : null}

      <FormField
        id="selected-customer-id"
        label="Selected customer"
        value={selectedCustomerId}
        onChange={setSelectedCustomerId}
      />
      <ActionButton onClick={() => void loadSelectedCustomerHistory()} disabled={isBusy || !selectedCustomerId}>
        Load selected customer history
      </ActionButton>

      {customerHistory ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Sales history</h3>
          <DetailList
            items={[
              { label: 'Sales', value: String(customerHistory.sales_summary.sales_count) },
              { label: 'Returns', value: String(customerHistory.sales_summary.return_count) },
              { label: 'Exchanges', value: String(customerHistory.sales_summary.exchange_count) },
              { label: 'Sales total', value: String(customerHistory.sales_summary.sales_total) },
            ]}
          />

          <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
            {customerHistory.sales.map((record) => (
              <li key={record.sale_id}>
                {record.invoice_number} - {record.payment_method} - {record.grand_total}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
