import { useEffect, useState } from 'react';
import { ActionButton, DetailList, FormField, SectionCard } from '@store/ui';
import type { ControlPlaneDeviceRecord, ControlPlanePrintJob } from '@store/types';
import { ownerControlPlaneClient } from './client';

type OwnerBarcodePrintRuntimeSectionProps = {
  accessToken: string;
  tenantId: string;
  branchId: string;
  productId: string;
  devices: ControlPlaneDeviceRecord[];
};

export function OwnerBarcodePrintRuntimeSection({
  accessToken,
  tenantId,
  branchId,
  productId,
  devices,
}: OwnerBarcodePrintRuntimeSectionProps) {
  const [selectedDeviceId, setSelectedDeviceId] = useState('');
  const [copies, setCopies] = useState('1');
  const [latestPrintJob, setLatestPrintJob] = useState<ControlPlanePrintJob | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  useEffect(() => {
    if (!selectedDeviceId && devices[0]?.id) {
      setSelectedDeviceId(devices[0].id);
    }
  }, [devices, selectedDeviceId]);

  async function queueBarcodeLabels() {
    if (!accessToken || !tenantId || !branchId || !productId || !selectedDeviceId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const printJob = await ownerControlPlaneClient.queueBarcodeLabelPrintJob(accessToken, tenantId, branchId, productId, {
        device_id: selectedDeviceId,
        copies: Number(copies),
      });
      setLatestPrintJob(printJob);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to queue barcode labels');
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <SectionCard eyebrow="Barcode print runtime" title="Barcode label queue">
      <p style={{ margin: 0, color: '#4e5871' }}>Queue branch-priced barcode labels onto an active runtime device on the control plane.</p>

      <div style={{ height: '16px' }} />

      <FormField
        id="barcode-runtime-device-id"
        label="Runtime device"
        value={selectedDeviceId}
        onChange={setSelectedDeviceId}
        placeholder={devices[0]?.id ?? 'Register a branch device first'}
      />
      <FormField id="barcode-label-copies" label="Label copies" value={copies} onChange={setCopies} />

      <ActionButton
        onClick={() => void queueBarcodeLabels()}
        disabled={isBusy || !accessToken || !tenantId || !branchId || !productId || !selectedDeviceId}
      >
        Queue barcode labels
      </ActionButton>

      <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
        {devices.length ? (
          devices.map((device) => (
            <li key={device.id}>
              {device.device_name} :: {device.device_code} :: {device.status}
            </li>
          ))
        ) : (
          <li>No active branch devices loaded yet.</li>
        )}
      </ul>

      {latestPrintJob ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Queued barcode label job</h3>
          <DetailList
            items={[
              { label: 'Print job', value: latestPrintJob.id },
              { label: 'Type', value: latestPrintJob.job_type },
              { label: 'Status', value: latestPrintJob.status },
              { label: 'Copies', value: String(latestPrintJob.copies) },
            ]}
          />
          <ul style={{ marginBottom: 0, marginTop: '16px', color: '#4e5871', lineHeight: 1.7 }}>
            {(latestPrintJob.payload.labels ?? []).map((label, index) => (
              <li key={`${label.barcode}-${index}`}>
                {label.product_name} :: {label.barcode} :: {label.price_label}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{errorMessage}</p> : null}
    </SectionCard>
  );
}
