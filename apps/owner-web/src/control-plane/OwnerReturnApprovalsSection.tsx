import { startTransition, useState } from 'react';
import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { ControlPlaneSaleReturn, ControlPlaneSaleReturnRecord } from '@store/types';
import { ownerControlPlaneClient } from './client';


type OwnerReturnApprovalsSectionProps = {
  accessToken: string;
  tenantId: string;
  branchId: string;
};

export function OwnerReturnApprovalsSection({ accessToken, tenantId, branchId }: OwnerReturnApprovalsSectionProps) {
  const [records, setRecords] = useState<ControlPlaneSaleReturnRecord[]>([]);
  const [selectedSaleReturnId, setSelectedSaleReturnId] = useState('');
  const [approvalNote, setApprovalNote] = useState('');
  const [latestApprovedReturn, setLatestApprovedReturn] = useState<ControlPlaneSaleReturn | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  async function loadRefundApprovals() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const response = await ownerControlPlaneClient.listSaleReturns(accessToken, tenantId, branchId);
      startTransition(() => {
        setRecords(response.records);
        setSelectedSaleReturnId(response.records[0]?.sale_return_id ?? '');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load refund approvals');
    } finally {
      setIsBusy(false);
    }
  }

  async function approveSelectedRefund() {
    if (!accessToken || !tenantId || !branchId || !selectedSaleReturnId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const approved = await ownerControlPlaneClient.approveSaleReturnRefund(accessToken, tenantId, branchId, selectedSaleReturnId, {
        note: approvalNote || null,
      });
      const response = await ownerControlPlaneClient.listSaleReturns(accessToken, tenantId, branchId);
      startTransition(() => {
        setLatestApprovedReturn(approved);
        setRecords(response.records);
        setSelectedSaleReturnId(response.records[0]?.sale_return_id ?? '');
        setApprovalNote('');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to approve refund');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <SectionCard eyebrow="Refund control plane" title="Refund approvals">
      <ActionButton onClick={() => void loadRefundApprovals()} disabled={isBusy || !accessToken || !tenantId || !branchId}>
        Load refund approvals
      </ActionButton>

      {records.length > 0 ? (
        <>
          <ul style={{ marginBottom: '16px', marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
            {records.map((record) => (
              <li key={record.sale_return_id}>
                {record.credit_note_number} - {record.customer_name} - {record.status}
              </li>
            ))}
          </ul>

          <FormField id="approval-note" label="Approval note" value={approvalNote} onChange={setApprovalNote} />
          <ActionButton onClick={() => void approveSelectedRefund()} disabled={isBusy || !selectedSaleReturnId}>
            Approve selected refund
          </ActionButton>
        </>
      ) : null}

      {latestApprovedReturn ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Latest approved refund</h3>
          <DetailList
            items={[
              { label: 'Credit note', value: latestApprovedReturn.credit_note.credit_note_number },
              { label: 'Refund', value: `${latestApprovedReturn.refund_method} ${latestApprovedReturn.refund_amount}` },
              {
                label: 'Status',
                value: <StatusBadge label={latestApprovedReturn.status} tone={latestApprovedReturn.status === 'REFUND_APPROVED' ? 'success' : 'warning'} />,
              },
            ]}
          />
        </div>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
