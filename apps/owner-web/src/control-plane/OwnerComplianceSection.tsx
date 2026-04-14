import { startTransition, useState } from 'react';
import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type {
  ControlPlaneComplianceProviderProfile,
  ControlPlaneGstExportJob,
  ControlPlaneGstExportReport,
  ControlPlaneSaleRecord,
} from '@store/types';
import { ownerControlPlaneClient } from './client';

type OwnerComplianceSectionProps = {
  accessToken: string;
  tenantId: string;
  branchId: string;
};

function firstPendingB2BSale(records: ControlPlaneSaleRecord[]): ControlPlaneSaleRecord | undefined {
  return records.find((record) => record.invoice_kind === 'B2B' && record.irn_status === 'IRN_PENDING');
}

function firstRetryableExport(records: ControlPlaneGstExportJob[]): ControlPlaneGstExportJob | undefined {
  return records.find((record) => record.status === 'ACTION_REQUIRED');
}

function statusTone(status: string): 'neutral' | 'success' | 'warning' {
  if (status === 'IRN_ATTACHED' || status === 'CONFIGURED') {
    return 'success';
  }
  if (status === 'ACTION_REQUIRED' || status === 'MISSING_PROFILE' || status === 'REQUEST_REJECTED') {
    return 'warning';
  }
  return 'neutral';
}

export function OwnerComplianceSection({ accessToken, tenantId, branchId }: OwnerComplianceSectionProps) {
  const [sales, setSales] = useState<ControlPlaneSaleRecord[]>([]);
  const [report, setReport] = useState<ControlPlaneGstExportReport | null>(null);
  const [profile, setProfile] = useState<ControlPlaneComplianceProviderProfile | null>(null);
  const [selectedSaleId, setSelectedSaleId] = useState('');
  const [selectedJobId, setSelectedJobId] = useState('');
  const [latestJob, setLatestJob] = useState<ControlPlaneGstExportJob | null>(null);
  const [providerName, setProviderName] = useState('iris_direct');
  const [apiUsername, setApiUsername] = useState('');
  const [apiPassword, setApiPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  async function loadComplianceQueue() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const [salesResponse, reportResponse, profileResponse] = await Promise.all([
        ownerControlPlaneClient.listSales(accessToken, tenantId, branchId),
        ownerControlPlaneClient.listGstExports(accessToken, tenantId, branchId),
        ownerControlPlaneClient.getComplianceProviderProfile(accessToken, tenantId, branchId),
      ]);
      const pendingSale = firstPendingB2BSale(salesResponse.records);
      const retryableExport = firstRetryableExport(reportResponse.records);
      startTransition(() => {
        setSales(salesResponse.records);
        setReport(reportResponse);
        setProfile(profileResponse);
        setProviderName(profileResponse.provider_name ?? 'iris_direct');
        setApiUsername(profileResponse.api_username ?? '');
        setSelectedSaleId(pendingSale?.sale_id ?? salesResponse.records[0]?.sale_id ?? '');
        setSelectedJobId(retryableExport?.id ?? reportResponse.records[0]?.id ?? '');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load compliance queue');
    } finally {
      setIsBusy(false);
    }
  }

  async function saveProviderProfile() {
    if (!accessToken || !tenantId || !branchId || !providerName || !apiUsername || !apiPassword) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const saved = await ownerControlPlaneClient.updateComplianceProviderProfile(accessToken, tenantId, branchId, {
        provider_name: providerName,
        api_username: apiUsername,
        api_password: apiPassword,
      });
      startTransition(() => {
        setProfile(saved);
        setApiPassword('');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to save provider profile');
    } finally {
      setIsBusy(false);
    }
  }

  async function createExportForSelectedSale() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    const saleId = selectedSaleId || firstPendingB2BSale(sales)?.sale_id;
    if (!saleId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const job = await ownerControlPlaneClient.createGstExport(accessToken, tenantId, branchId, { sale_id: saleId });
      const refreshedReport = await ownerControlPlaneClient.listGstExports(accessToken, tenantId, branchId);
      startTransition(() => {
        setLatestJob(job);
        setReport(refreshedReport);
        setSelectedJobId(firstRetryableExport(refreshedReport.records)?.id ?? job.id);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to create GST export');
    } finally {
      setIsBusy(false);
    }
  }

  async function retrySelectedExport() {
    if (!accessToken || !tenantId || !branchId || !selectedJobId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const retried = await ownerControlPlaneClient.retryGstExportSubmission(accessToken, tenantId, branchId, selectedJobId);
      const refreshedReport = await ownerControlPlaneClient.listGstExports(accessToken, tenantId, branchId);
      startTransition(() => {
        setLatestJob(retried);
        setReport(refreshedReport);
        setSelectedJobId(retried.id);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to retry GST export');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <SectionCard eyebrow="Compliance foundation" title="IRP submission queue">
      <ActionButton onClick={() => void loadComplianceQueue()} disabled={isBusy || !accessToken || !tenantId || !branchId}>
        Load compliance queue
      </ActionButton>

      <div style={{ marginTop: '16px' }}>
        <FormField id="provider-name" label="Provider" value={providerName} onChange={setProviderName} />
        <FormField id="api-username" label="API username" value={apiUsername} onChange={setApiUsername} />
        <FormField id="api-password" label="API password" value={apiPassword} onChange={setApiPassword} />
        <ActionButton onClick={() => void saveProviderProfile()} disabled={isBusy || !providerName || !apiUsername || !apiPassword}>
          Save provider profile
        </ActionButton>
      </div>

      {profile ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Provider profile</h3>
          <DetailList
            items={[
              { label: 'Provider', value: profile.provider_name ?? 'Not configured' },
              { label: 'Username', value: profile.api_username ?? 'Unavailable' },
              { label: 'Password saved', value: profile.has_password ? 'Yes' : 'No' },
              { label: 'Status', value: <StatusBadge label={profile.status} tone={statusTone(profile.status)} /> },
            ]}
          />
          {profile.last_error_message ? (
            <p style={{ color: '#9d2b19', marginBottom: 0, marginTop: '12px' }}>{profile.last_error_message}</p>
          ) : null}
        </div>
      ) : null}

      {report ? (
        <div style={{ marginTop: '16px' }}>
          <DetailList
            items={[
              { label: 'Pending', value: String(report.pending_count) },
              { label: 'Attached', value: String(report.attached_count) },
            ]}
          />
        </div>
      ) : null}

      {sales.length > 0 ? (
        <ul style={{ marginBottom: '16px', marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {sales.map((record) => (
            <li key={record.sale_id}>
              {record.invoice_number} - {record.customer_name} - {record.irn_status}
            </li>
          ))}
        </ul>
      ) : null}

      <ActionButton onClick={() => void createExportForSelectedSale()} disabled={isBusy || !selectedSaleId}>
        Queue export for first pending invoice
      </ActionButton>

      {report?.records.length ? (
        <ul style={{ marginBottom: '16px', marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {report.records.map((record) => (
            <li key={record.id}>
              {record.invoice_number} - {record.status}
              {record.provider_status ? ` - ${record.provider_status}` : ''}
              {record.last_error_message ? ` - ${record.last_error_message}` : ''}
            </li>
          ))}
        </ul>
      ) : null}

      <ActionButton
        onClick={() => void retrySelectedExport()}
        disabled={isBusy || !selectedJobId || !(report?.records.some((record) => record.id === selectedJobId && record.status === 'ACTION_REQUIRED'))}
      >
        Retry selected export
      </ActionButton>

      {latestJob ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Latest GST export job</h3>
          <DetailList
            items={[
              { label: 'Invoice', value: latestJob.invoice_number },
              {
                label: 'Status',
                value: <StatusBadge label={latestJob.status} tone={statusTone(latestJob.status)} />,
              },
              {
                label: 'Provider',
                value: latestJob.provider_status ? (
                  <StatusBadge label={latestJob.provider_status} tone={statusTone(latestJob.provider_status)} />
                ) : (
                  'Unavailable'
                ),
              },
              { label: 'IRN', value: latestJob.irn ?? 'Unavailable' },
              { label: 'Ack', value: latestJob.ack_no ?? 'Unavailable' },
            ]}
          />
          {latestJob.last_error_message ? (
            <p style={{ color: '#9d2b19', marginBottom: 0, marginTop: '12px' }}>{latestJob.last_error_message}</p>
          ) : null}
        </div>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
