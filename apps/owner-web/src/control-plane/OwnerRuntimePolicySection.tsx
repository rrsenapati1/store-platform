import { useState } from 'react';
import { ActionButton, DetailList, SectionCard, StatusBadge } from '@store/ui';
import type { ControlPlaneBranchRuntimePolicy } from '@store/types';
import { ownerControlPlaneClient } from './client';

type OwnerRuntimePolicySectionProps = {
  accessToken: string;
  tenantId: string;
  branchId: string;
};

const defaultPolicy: ControlPlaneBranchRuntimePolicy = {
  id: null,
  tenant_id: '',
  branch_id: '',
  require_shift_for_attendance: false,
  require_attendance_for_cashier: true,
  require_assigned_staff_for_device: true,
  allow_offline_sales: true,
  max_pending_offline_sales: 25,
  updated_by_user_id: null,
};

function ToggleRow(props: {
  id: string;
  label: string;
  checked: boolean;
  disabled: boolean;
  onChange(nextValue: boolean): void;
}) {
  return (
    <label htmlFor={props.id} style={{ alignItems: 'center', cursor: props.disabled ? 'not-allowed' : 'pointer', display: 'flex', gap: '10px' }}>
      <input
        id={props.id}
        type="checkbox"
        checked={props.checked}
        disabled={props.disabled}
        onChange={(event) => props.onChange(event.target.checked)}
      />
      <span>{props.label}</span>
    </label>
  );
}

export function OwnerRuntimePolicySection({
  accessToken,
  tenantId,
  branchId,
}: OwnerRuntimePolicySectionProps) {
  const [policy, setPolicy] = useState<ControlPlaneBranchRuntimePolicy>(defaultPolicy);
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  async function loadRuntimePolicy() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const response = await ownerControlPlaneClient.getBranchRuntimePolicy(accessToken, tenantId, branchId);
      setPolicy(response);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load runtime policy.');
    } finally {
      setIsBusy(false);
    }
  }

  async function saveRuntimePolicy() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const response = await ownerControlPlaneClient.updateBranchRuntimePolicy(accessToken, tenantId, branchId, {
        require_shift_for_attendance: policy.require_shift_for_attendance,
        require_attendance_for_cashier: policy.require_attendance_for_cashier,
        require_assigned_staff_for_device: policy.require_assigned_staff_for_device,
        allow_offline_sales: policy.allow_offline_sales,
        max_pending_offline_sales: policy.max_pending_offline_sales,
      });
      setPolicy(response);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to save runtime policy.');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <SectionCard eyebrow="Branch runtime policy" title="Runtime controls">
      <div style={{ display: 'grid', gap: '12px' }}>
        <ToggleRow
          id="owner-policy-require-shift"
          label="Require an open shift before attendance"
          checked={policy.require_shift_for_attendance}
          disabled={isBusy || !accessToken || !tenantId || !branchId}
          onChange={(nextValue) => setPolicy((current) => ({ ...current, require_shift_for_attendance: nextValue }))}
        />
        <ToggleRow
          id="owner-policy-require-attendance"
          label="Require attendance before cashier opening"
          checked={policy.require_attendance_for_cashier}
          disabled={isBusy || !accessToken || !tenantId || !branchId}
          onChange={(nextValue) => setPolicy((current) => ({ ...current, require_attendance_for_cashier: nextValue }))}
        />
        <ToggleRow
          id="owner-policy-require-assignment"
          label="Require assigned staff on runtime devices"
          checked={policy.require_assigned_staff_for_device}
          disabled={isBusy || !accessToken || !tenantId || !branchId}
          onChange={(nextValue) => setPolicy((current) => ({ ...current, require_assigned_staff_for_device: nextValue }))}
        />
        <ToggleRow
          id="owner-policy-allow-offline-sales"
          label="Allow offline sales continuity"
          checked={policy.allow_offline_sales}
          disabled={isBusy || !accessToken || !tenantId || !branchId}
          onChange={(nextValue) => setPolicy((current) => ({ ...current, allow_offline_sales: nextValue }))}
        />
        <label htmlFor="owner-policy-max-pending-offline-sales" style={{ color: '#25314f', display: 'grid', fontWeight: 600, gap: '6px' }}>
          <span>Max pending offline sales</span>
          <input
            id="owner-policy-max-pending-offline-sales"
            type="number"
            min={0}
            value={policy.max_pending_offline_sales}
            disabled={isBusy || !accessToken || !tenantId || !branchId}
            onChange={(event) => setPolicy((current) => ({
              ...current,
              max_pending_offline_sales: Number.parseInt(event.target.value || '0', 10),
            }))}
            style={{ border: '1px solid #d4d9e2', borderRadius: '10px', padding: '10px 12px' }}
          />
        </label>
      </div>

      <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
        <ActionButton onClick={() => void saveRuntimePolicy()} disabled={isBusy || !accessToken || !tenantId || !branchId}>
          Save runtime policy
        </ActionButton>
        <ActionButton onClick={() => void loadRuntimePolicy()} disabled={isBusy || !accessToken || !tenantId || !branchId}>
          Reload policy
        </ActionButton>
      </div>

      <div style={{ marginTop: '16px' }}>
        <DetailList
          items={[
            { label: 'Shift gate', value: <StatusBadge label={policy.require_shift_for_attendance ? 'REQUIRED' : 'OPTIONAL'} tone={policy.require_shift_for_attendance ? 'warning' : 'neutral'} /> },
            { label: 'Attendance gate', value: <StatusBadge label={policy.require_attendance_for_cashier ? 'REQUIRED' : 'OPTIONAL'} tone={policy.require_attendance_for_cashier ? 'warning' : 'neutral'} /> },
            { label: 'Assigned staff gate', value: <StatusBadge label={policy.require_assigned_staff_for_device ? 'REQUIRED' : 'OPTIONAL'} tone={policy.require_assigned_staff_for_device ? 'warning' : 'neutral'} /> },
            { label: 'Offline sales', value: <StatusBadge label={policy.allow_offline_sales ? 'ALLOWED' : 'BLOCKED'} tone={policy.allow_offline_sales ? 'success' : 'warning'} /> },
            { label: 'Pending offline limit', value: String(policy.max_pending_offline_sales) },
          ]}
        />
      </div>

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
