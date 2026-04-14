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
        <ActionButton onClick={() => void workspace.completeFirstPrintJob()} disabled={workspace.isBusy || !workspace.isSessionLive || workspace.printJobs.length === 0 || !hasDevice}>
          Mark first job completed
        </ActionButton>
      </div>

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
