import { startTransition, useMemo, useState } from 'react';
import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { ControlPlaneDeviceClaimApproval, ControlPlaneDeviceClaimRecord } from '@store/types';
import { ownerControlPlaneClient } from './client';

type OwnerDeviceClaimSectionProps = {
  accessToken: string;
  tenantId: string;
  branchId: string;
  onApproved?: (approval: ControlPlaneDeviceClaimApproval) => void;
};

function buildClaimTone(status: string) {
  return status === 'APPROVED' ? 'success' : 'warning';
}

export function OwnerDeviceClaimSection({
  accessToken,
  tenantId,
  branchId,
  onApproved,
}: OwnerDeviceClaimSectionProps) {
  const [claims, setClaims] = useState<ControlPlaneDeviceClaimRecord[]>([]);
  const [selectedClaimId, setSelectedClaimId] = useState('');
  const [deviceName, setDeviceName] = useState('');
  const [deviceCode, setDeviceCode] = useState('');
  const [latestApproval, setLatestApproval] = useState<ControlPlaneDeviceClaimApproval | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  const selectedClaim = useMemo(
    () => claims.find((claim) => claim.id === selectedClaimId) ?? claims[0] ?? null,
    [claims, selectedClaimId],
  );

  async function loadClaims() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const response = await ownerControlPlaneClient.listBranchDeviceClaims(accessToken, tenantId, branchId);
      startTransition(() => {
        setClaims(response.records);
        setSelectedClaimId(response.records[0]?.id ?? '');
        setLatestApproval(null);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load device claims');
    } finally {
      setIsBusy(false);
    }
  }

  async function approveSelectedClaim() {
    if (!accessToken || !tenantId || !branchId || !selectedClaim || !deviceName || !deviceCode) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const approval = await ownerControlPlaneClient.approveBranchDeviceClaim(
        accessToken,
        tenantId,
        branchId,
        selectedClaim.id,
        {
          device_name: deviceName,
          device_code: deviceCode,
          session_surface: 'store_desktop',
        },
      );
      startTransition(() => {
        setLatestApproval(approval);
        setClaims((currentClaims) =>
          currentClaims.map((claim) => (claim.id === approval.claim.id ? approval.claim : claim)),
        );
        setSelectedClaimId(approval.claim.id);
        setDeviceName('');
        setDeviceCode('');
      });
      onApproved?.(approval);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to approve selected claim');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <SectionCard eyebrow="Packaged device binding" title="Pending packaged-runtime claims">
      <ActionButton onClick={() => void loadClaims()} disabled={isBusy || !accessToken || !tenantId || !branchId}>
        Load device claims
      </ActionButton>

      {claims.length ? (
        <ul style={{ marginBottom: '16px', marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
          {claims.map((claim) => (
            <li key={claim.id}>
              <button
                type="button"
                onClick={() => setSelectedClaimId(claim.id)}
                style={{
                  border: 0,
                  background: 'transparent',
                  padding: 0,
                  cursor: 'pointer',
                  color: claim.id === selectedClaim?.id ? '#172033' : '#4e5871',
                  fontWeight: claim.id === selectedClaim?.id ? 700 : 400,
                }}
              >
                {claim.claim_code}
              </button>{' '}
              <span>:: {claim.hostname ?? 'Unknown host'} :: </span>
              <StatusBadge label={claim.status} tone={buildClaimTone(claim.status)} />
            </li>
          ))}
        </ul>
      ) : null}

      {selectedClaim ? (
        <div style={{ marginBottom: '16px' }}>
          <DetailList
            items={[
              { label: 'Runtime kind', value: selectedClaim.runtime_kind },
              { label: 'Hostname', value: selectedClaim.hostname ?? 'Unavailable' },
              { label: 'Platform', value: `${selectedClaim.operating_system ?? 'unknown'} / ${selectedClaim.architecture ?? 'unknown'}` },
            ]}
          />
        </div>
      ) : null}

      <FormField id="device-claim-device-name" label="Approved device name" value={deviceName} onChange={setDeviceName} />
      <FormField id="device-claim-device-code" label="Approved device code" value={deviceCode} onChange={setDeviceCode} />
      <ActionButton
        onClick={() => void approveSelectedClaim()}
        disabled={isBusy || !selectedClaim || selectedClaim?.status === 'APPROVED' || !deviceName || !deviceCode}
      >
        Approve selected claim
      </ActionButton>

      {latestApproval ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Approved runtime device</h3>
          <DetailList
            items={[
              { label: 'Claim', value: latestApproval.claim.claim_code },
              { label: 'Device', value: latestApproval.device.device_name },
              { label: 'Device code', value: latestApproval.device.device_code },
            ]}
          />
        </div>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
