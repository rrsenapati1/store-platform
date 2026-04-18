import { useState } from 'react';
import { ActionButton, SectionCard } from '@store/ui';
import type { ControlPlaneAuditRecord } from '@store/types';
import { ownerControlPlaneClient } from './client';

type OwnerWorkforceAuditSectionProps = {
  accessToken: string;
  tenantId: string;
  branchId: string;
};

export function OwnerWorkforceAuditSection({
  accessToken,
  tenantId,
  branchId,
}: OwnerWorkforceAuditSectionProps) {
  const [records, setRecords] = useState<ControlPlaneAuditRecord[]>([]);
  const [csvPreview, setCsvPreview] = useState('');
  const [csvFilename, setCsvFilename] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  async function loadAuditEvents() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const response = await ownerControlPlaneClient.listBranchWorkforceAuditEvents(accessToken, tenantId, branchId);
      setRecords(response.records);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load workforce audit events.');
    } finally {
      setIsBusy(false);
    }
  }

  async function exportAuditEvents() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const response = await ownerControlPlaneClient.exportBranchWorkforceAuditEvents(accessToken, tenantId, branchId);
      setCsvFilename(response.filename);
      setCsvPreview(response.content);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to export workforce audit events.');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <SectionCard eyebrow="Branch workforce audit" title="Audit and export">
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <ActionButton onClick={() => void loadAuditEvents()} disabled={isBusy || !accessToken || !tenantId || !branchId}>
          Refresh workforce audit
        </ActionButton>
        <ActionButton onClick={() => void exportAuditEvents()} disabled={isBusy || !accessToken || !tenantId || !branchId}>
          Export workforce audit CSV
        </ActionButton>
      </div>

      {records.length ? (
        <ul style={{ color: '#4e5871', lineHeight: 1.7, marginBottom: 0, marginTop: '16px' }}>
          {records.map((record) => (
            <li key={record.id}>
              {record.action} :: {record.entity_type} :: {record.entity_id}
            </li>
          ))}
        </ul>
      ) : (
        <p style={{ color: '#4e5871', marginBottom: 0, marginTop: '16px' }}>
          Load workforce audit events to inspect branch policy, shift, attendance, and cashier governance actions.
        </p>
      )}

      {csvPreview ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Latest export preview</h3>
          <p style={{ color: '#4e5871', marginBottom: '10px' }}>{csvFilename}</p>
          <pre style={{ background: '#f3f5f8', borderRadius: '12px', margin: 0, maxHeight: '240px', overflow: 'auto', padding: '12px', whiteSpace: 'pre-wrap' }}>
            {csvPreview}
          </pre>
        </div>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
