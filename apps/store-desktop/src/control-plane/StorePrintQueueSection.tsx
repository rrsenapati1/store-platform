import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function describePrintJobPayload(job: StoreRuntimeWorkspaceState['printJobs'][number]) {
  if (job.payload.document_number) {
    return job.payload.document_number;
  }
  if (job.payload.labels?.length) {
    const label = job.payload.labels[0];
    return `${label.product_name} :: ${label.price_label}`;
  }
  return 'Pending payload';
}

export function StorePrintQueueSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const hasDevice = Boolean(workspace.selectedRuntimeDeviceId);
  const latestJob = workspace.latestPrintJob;
  const isPackagedRuntime = workspace.runtimeShellKind === 'packaged_desktop';
  const runtimeHardwareScales = workspace.runtimeHardwareScales ?? [];
  const preferredScaleLabel = runtimeHardwareScales.find(
    (scale) => scale.id === workspace.runtimePreferredScaleId,
  )?.label ?? workspace.runtimePreferredScaleId;

  return (
    <SectionCard eyebrow="Runtime print desk" title="Print queue and device polling">
      <FormField
        id="runtime-device-id"
        label="Runtime device"
        value={workspace.selectedRuntimeDeviceId}
        onChange={workspace.setSelectedRuntimeDeviceId}
        placeholder="device-id"
      />

      <ul style={{ marginTop: '12px', marginBottom: '16px', color: '#4e5871', lineHeight: 1.7 }}>
        {workspace.runtimeDevices.length ? (
          workspace.runtimeDevices.map((device) => (
            <li key={device.id}>
              <strong>{device.device_name}</strong>
              <span> :: {device.device_code} :: {device.status}</span>
            </li>
          ))
        ) : (
          <li>No runtime devices registered for this branch yet.</li>
        )}
      </ul>

      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        <ActionButton onClick={() => void workspace.queueLatestInvoicePrint()} disabled={workspace.isBusy || !workspace.isSessionLive || !workspace.latestSale || !hasDevice}>
          Queue latest invoice print
        </ActionButton>
        <ActionButton onClick={() => void workspace.queueLatestCreditNotePrint()} disabled={workspace.isBusy || !workspace.isSessionLive || !workspace.latestSaleReturn || !hasDevice}>
          Queue latest credit note print
        </ActionButton>
        <ActionButton onClick={() => void workspace.heartbeatRuntimeDevice()} disabled={workspace.isBusy || !workspace.isSessionLive || !hasDevice}>
          Send device heartbeat
        </ActionButton>
        <ActionButton onClick={() => void workspace.refreshPrintQueue()} disabled={workspace.isBusy || !workspace.isSessionLive || !hasDevice}>
          Refresh print queue
        </ActionButton>
        {isPackagedRuntime ? (
          <ActionButton
            onClick={() => void workspace.openRuntimeCashDrawer()}
            disabled={workspace.isBusy || !workspace.isSessionLive || !workspace.runtimeCashDrawerPrinterName}
          >
            Open assigned cash drawer
          </ActionButton>
        ) : null}
        {isPackagedRuntime ? (
          <ActionButton
            onClick={() => void workspace.readRuntimeScaleWeight()}
            disabled={workspace.isBusy || !workspace.isSessionLive || !workspace.runtimePreferredScaleId}
          >
            Read current weight
          </ActionButton>
        ) : null}
        {!isPackagedRuntime ? (
          <ActionButton onClick={() => void workspace.completeFirstPrintJob()} disabled={workspace.isBusy || !workspace.isSessionLive || workspace.printJobs.length === 0 || !hasDevice}>
            Mark first job completed
          </ActionButton>
        ) : null}
      </div>

      {isPackagedRuntime ? (
        <div style={{ marginTop: '18px' }}>
          <DetailList
            items={[
              { label: 'Hardware bridge', value: workspace.runtimeHardwareBridgeState ?? 'Unavailable' },
              { label: 'Receipt printer', value: workspace.runtimeReceiptPrinterName ?? 'Not assigned' },
              { label: 'Label printer', value: workspace.runtimeLabelPrinterName ?? 'Not assigned' },
              { label: 'Cash drawer', value: workspace.runtimeCashDrawerPrinterName ?? 'Not assigned' },
              { label: 'Weighing scale', value: preferredScaleLabel ?? 'Not assigned' },
              { label: 'Scale status', value: workspace.runtimeScaleStatusMessage ?? 'No scale diagnostics available' },
              { label: 'Scale setup hint', value: workspace.runtimeScaleSetupHint ?? 'No scale setup guidance available' },
              {
                label: 'Last weight',
                value: workspace.runtimeScaleLastWeightValue !== null && workspace.runtimeScaleLastWeightUnit
                  ? `${workspace.runtimeScaleLastWeightValue} ${workspace.runtimeScaleLastWeightUnit}`
                  : 'No live weight captured yet',
              },
              { label: 'Cash drawer status', value: workspace.runtimeCashDrawerStatusMessage ?? 'No cash drawer diagnostics available' },
              { label: 'Cash drawer setup hint', value: workspace.runtimeCashDrawerSetupHint ?? 'No cash drawer setup guidance available' },
              { label: 'Last cash drawer action', value: workspace.runtimeHardwareLastCashDrawerMessage ?? 'No cash drawer activity yet' },
              { label: 'Last local print', value: workspace.runtimeHardwareLastPrintMessage ?? 'No local print activity yet' },
            ]}
          />
        </div>
      ) : null}

      {isPackagedRuntime ? (
        <div style={{ marginTop: '18px' }}>
          <h3 style={{ marginBottom: '10px' }}>Discovered local printers</h3>
          <ul style={{ margin: 0, color: '#4e5871', lineHeight: 1.7 }}>
            {workspace.runtimeHardwarePrinters.length ? (
              workspace.runtimeHardwarePrinters.map((printer) => (
                <li key={printer.name} style={{ marginBottom: '12px' }}>
                  <strong>{printer.label}</strong>
                  <span> :: {printer.is_default ? 'default' : 'secondary'} :: {printer.is_online === false ? 'offline' : 'ready'}</span>
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '8px' }}>
                    <ActionButton onClick={() => void workspace.assignRuntimeReceiptPrinter(printer.name)} disabled={workspace.isBusy}>
                      Use for receipts
                    </ActionButton>
                    <ActionButton onClick={() => void workspace.assignRuntimeLabelPrinter(printer.name)} disabled={workspace.isBusy}>
                      Use for labels
                    </ActionButton>
                    <ActionButton onClick={() => void workspace.assignRuntimeCashDrawerPrinter(printer.name)} disabled={workspace.isBusy}>
                      Use for cash drawer
                    </ActionButton>
                  </div>
                </li>
              ))
            ) : (
              <li>No local printers discovered yet.</li>
            )}
          </ul>
          {workspace.runtimeHardwareError ? (
            <p style={{ color: '#9d2b19', marginBottom: 0 }}>{workspace.runtimeHardwareError}</p>
          ) : null}
        </div>
      ) : null}

      {isPackagedRuntime ? (
        <div style={{ marginTop: '18px' }}>
          <h3 style={{ marginBottom: '10px' }}>Discovered local scales</h3>
          <ul style={{ margin: 0, color: '#4e5871', lineHeight: 1.7 }}>
            {runtimeHardwareScales.length ? (
              runtimeHardwareScales.map((scale) => (
                <li key={scale.id} style={{ marginBottom: '12px' }}>
                  <strong>{scale.label}</strong>
                  <span> :: {scale.transport} :: {scale.is_connected ? 'connected' : 'disconnected'}</span>
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '8px' }}>
                    <ActionButton onClick={() => void workspace.assignRuntimePreferredScale(scale.id)} disabled={workspace.isBusy}>
                      Use for weighing scale
                    </ActionButton>
                  </div>
                </li>
              ))
            ) : (
              <li>No local serial scale candidates discovered yet.</li>
            )}
          </ul>
        </div>
      ) : null}

      {workspace.runtimeHeartbeat ? (
        <div style={{ marginTop: '18px' }}>
          <DetailList
            items={[
              { label: 'Heartbeat status', value: workspace.runtimeHeartbeat.status },
              { label: 'Queued jobs', value: String(workspace.runtimeHeartbeat.queued_job_count) },
              { label: 'Last seen', value: workspace.runtimeHeartbeat.last_seen_at ?? 'Not reported' },
            ]}
          />
        </div>
      ) : null}

      {latestJob ? (
        <div style={{ marginTop: '18px' }}>
          <h3 style={{ marginBottom: '10px' }}>{latestJob.status === 'QUEUED' ? 'Queued print job' : 'Latest print job'}</h3>
          <DetailList
            items={[
              { label: 'Print job', value: latestJob.id },
              { label: 'Type', value: latestJob.job_type },
              { label: 'Preview', value: describePrintJobPayload(latestJob) },
              {
                label: 'Status',
                value: (
                  <StatusBadge
                    label={latestJob.status}
                    tone={latestJob.status === 'COMPLETED' ? 'success' : 'warning'}
                  />
                ),
              },
            ]}
          />
        </div>
      ) : null}

      <div style={{ marginTop: '18px' }}>
        <h3 style={{ marginBottom: '10px' }}>Queued jobs: {workspace.printJobs.length}</h3>
        <ul style={{ margin: 0, color: '#4e5871', lineHeight: 1.7 }}>
          {workspace.printJobs.length ? (
            workspace.printJobs.map((job) => (
              <li key={job.id}>
                {job.id} :: {job.job_type} :: {describePrintJobPayload(job)}
              </li>
            ))
          ) : (
            <li>No queued print jobs loaded yet.</li>
          )}
        </ul>
      </div>
    </SectionCard>
  );
}
