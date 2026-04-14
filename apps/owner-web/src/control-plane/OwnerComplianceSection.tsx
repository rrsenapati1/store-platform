import { startTransition, useState } from 'react';
import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { ControlPlaneGstExportJob, ControlPlaneGstExportReport, ControlPlaneSaleRecord } from '@store/types';
import { ownerControlPlaneClient } from './client';


type OwnerComplianceSectionProps = {
  accessToken: string;
  tenantId: string;
  branchId: string;
};

function firstPendingB2BSale(records: ControlPlaneSaleRecord[]): ControlPlaneSaleRecord | undefined {
  return records.find((record) => record.invoice_kind === 'B2B' && record.irn_status === 'IRN_PENDING');
}

function firstAttachableExport(records: ControlPlaneGstExportJob[]): ControlPlaneGstExportJob | undefined {
  return records.find((record) => record.status === 'IRN_PENDING');
}

export function OwnerComplianceSection({ accessToken, tenantId, branchId }: OwnerComplianceSectionProps) {
  const [sales, setSales] = useState<ControlPlaneSaleRecord[]>([]);
  const [report, setReport] = useState<ControlPlaneGstExportReport | null>(null);
  const [selectedSaleId, setSelectedSaleId] = useState('');
  const [selectedJobId, setSelectedJobId] = useState('');
  const [latestJob, setLatestJob] = useState<ControlPlaneGstExportJob | null>(null);
  const [latestAttachment, setLatestAttachment] = useState<ControlPlaneGstExportJob | null>(null);
  const [irn, setIrn] = useState('');
  const [ackNo, setAckNo] = useState('');
  const [signedQrPayload, setSignedQrPayload] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  async function loadComplianceQueue() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const [salesResponse, reportResponse] = await Promise.all([
        ownerControlPlaneClient.listSales(accessToken, tenantId, branchId),
        ownerControlPlaneClient.listGstExports(accessToken, tenantId, branchId),
      ]);
      const pendingSale = firstPendingB2BSale(salesResponse.records);
      startTransition(() => {
        setSales(salesResponse.records);
        setReport(reportResponse);
        setSelectedSaleId(pendingSale?.sale_id ?? salesResponse.records[0]?.sale_id ?? '');
        setSelectedJobId(firstAttachableExport(reportResponse.records)?.id ?? '');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load compliance queue');
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
        setSelectedJobId(firstAttachableExport(refreshedReport.records)?.id ?? '');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to create GST export');
    } finally {
      setIsBusy(false);
    }
  }

  async function attachIrnToSelectedExport() {
    if (!accessToken || !tenantId || !branchId || !selectedJobId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const attached = await ownerControlPlaneClient.attachIrn(accessToken, tenantId, branchId, selectedJobId, {
        irn,
        ack_no: ackNo,
        signed_qr_payload: signedQrPayload,
      });
      const refreshedReport = await ownerControlPlaneClient.listGstExports(accessToken, tenantId, branchId);
      startTransition(() => {
        setLatestAttachment(attached);
        setReport(refreshedReport);
        setSelectedJobId(attached.id);
        setIrn('');
        setAckNo('');
        setSignedQrPayload('');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to attach IRN');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <SectionCard eyebrow="Compliance foundation" title="Compliance export jobs">
      <ActionButton onClick={() => void loadComplianceQueue()} disabled={isBusy || !accessToken || !tenantId || !branchId}>
        Load compliance queue
      </ActionButton>

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
        Create export for first pending invoice
      </ActionButton>

      {report?.records.length ? (
        <ul style={{ marginBottom: '16px', marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {report.records.map((record) => (
            <li key={record.id}>
              {record.invoice_number} - {record.status}
            </li>
          ))}
        </ul>
      ) : null}

      <FormField id="irn" label="IRN" value={irn} onChange={setIrn} />
      <FormField id="ack-number" label="Ack number" value={ackNo} onChange={setAckNo} />
      <FormField id="signed-qr-payload" label="Signed QR payload" value={signedQrPayload} onChange={setSignedQrPayload} />
      <ActionButton
        onClick={() => void attachIrnToSelectedExport()}
        disabled={isBusy || !selectedJobId || !irn || !ackNo || !signedQrPayload}
      >
        Attach IRN to selected export
      </ActionButton>

      {latestJob ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Latest GST export job</h3>
          <DetailList
            items={[
              { label: 'Invoice', value: latestJob.invoice_number },
              { label: 'Buyer GSTIN', value: latestJob.buyer_gstin ?? 'Unavailable' },
              { label: 'Status', value: <StatusBadge label={latestJob.status} tone="warning" /> },
            ]}
          />
          {latestJob.status === 'QUEUED' ? (
            <p style={{ color: '#4e5871', marginBottom: 0, marginTop: '12px' }}>Queued for worker preparation</p>
          ) : null}
        </div>
      ) : null}

      {latestAttachment ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Latest IRN attachment</h3>
          <DetailList
            items={[
              { label: 'Invoice', value: latestAttachment.invoice_number },
              { label: 'IRN', value: latestAttachment.irn ?? 'Unavailable' },
              { label: 'Ack', value: latestAttachment.ack_no ?? 'Unavailable' },
              { label: 'Status', value: <StatusBadge label={latestAttachment.status} tone="success" /> },
            ]}
          />
        </div>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
