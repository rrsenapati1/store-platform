import { startTransition, useEffect, useEffectEvent, useRef, useState } from 'react';
import type { ControlPlanePrintJob } from '@store/types';
import {
  createResolvedStoreRuntimeHardware,
  type StoreRuntimeHardwarePrintJobInput,
  type StoreRuntimeHardwareProfileInput,
  type StoreRuntimeHardwareStatus,
} from '../runtime-hardware/storeRuntimeHardware';
import { storeControlPlaneClient } from './client';

const HARDWARE_POLL_INTERVAL_MS = 2000;

function toHardwarePrintJob(job: ControlPlanePrintJob): StoreRuntimeHardwarePrintJobInput {
  return {
    job_id: job.id,
    job_type: job.job_type,
    document_number: job.payload.document_number ?? null,
    receipt_lines: job.payload.receipt_lines ?? null,
    labels: job.payload.labels ?? null,
  };
}

function shouldLeavePrintJobQueued(message: string) {
  return /must be assigned/i.test(message);
}

export function useStoreRuntimeHardwareIntegration(args: {
  runtimeShellKind: string | null;
  accessToken: string;
  tenantId: string;
  branchId: string;
  selectedRuntimeDeviceId: string;
  isSessionLive: boolean;
  isLocalUnlocked: boolean;
  pollIntervalMs?: number;
  onPrintJobsChange: (jobs: ControlPlanePrintJob[]) => void;
  onLatestPrintJobChange: (job: ControlPlanePrintJob | null) => void;
  onErrorMessage: (message: string) => void;
}) {
  const hardwareAdapterRef = useRef(createResolvedStoreRuntimeHardware());
  const [hardwareStatus, setHardwareStatus] = useState<StoreRuntimeHardwareStatus | null>(null);
  const [hardwareError, setHardwareError] = useState<string | null>(null);
  const printDispatchInFlightRef = useRef(false);

  const applyPrintJobsChange = useEffectEvent(args.onPrintJobsChange);
  const applyLatestPrintJobChange = useEffectEvent(args.onLatestPrintJobChange);
  const applyErrorMessage = useEffectEvent(args.onErrorMessage);

  const refreshHardwareStatus = useEffectEvent(async () => {
    const nextStatus = await hardwareAdapterRef.current.getStatus();
    startTransition(() => {
      setHardwareStatus(nextStatus);
      setHardwareError(null);
    });
    return nextStatus;
  });

  useEffect(() => {
    let isCancelled = false;

    void refreshHardwareStatus().catch((error) => {
      if (!isCancelled) {
        const message = error instanceof Error ? error.message : 'Unable to load runtime hardware status';
        startTransition(() => {
          setHardwareError(message);
        });
      }
    });

    return () => {
      isCancelled = true;
    };
  }, [refreshHardwareStatus]);

  useEffect(() => {
    if (
      args.runtimeShellKind !== 'packaged_desktop'
      || !args.isSessionLive
      || !args.isLocalUnlocked
      || !args.accessToken
      || !args.tenantId
      || !args.branchId
      || !args.selectedRuntimeDeviceId
    ) {
      return;
    }

    let isCancelled = false;

    const runPoll = async () => {
      if (printDispatchInFlightRef.current) {
        return;
      }
      printDispatchInFlightRef.current = true;
      try {
        const nextHardwareStatus = await hardwareAdapterRef.current.getStatus();
        if (isCancelled) {
          return;
        }
        startTransition(() => {
          setHardwareStatus(nextHardwareStatus);
          setHardwareError(null);
        });

        const queuedJobs = await storeControlPlaneClient.listRuntimePrintJobs(
          args.accessToken,
          args.tenantId,
          args.branchId,
          args.selectedRuntimeDeviceId,
        );
        if (isCancelled) {
          return;
        }
        startTransition(() => {
          applyPrintJobsChange(queuedJobs.records);
        });

        const nextJob = queuedJobs.records[0];
        if (!nextJob || nextHardwareStatus.bridge_state !== 'ready') {
          return;
        }

        try {
          const dispatchStatus = await hardwareAdapterRef.current.dispatchPrintJob(toHardwarePrintJob(nextJob));
          if (isCancelled) {
            return;
          }
          startTransition(() => {
            setHardwareStatus(dispatchStatus);
            setHardwareError(null);
          });

          const completed = await storeControlPlaneClient.completeRuntimePrintJob(
            args.accessToken,
            args.tenantId,
            args.branchId,
            args.selectedRuntimeDeviceId,
            nextJob.id,
            { status: 'COMPLETED' },
          );
          if (isCancelled) {
            return;
          }
          startTransition(() => {
            applyLatestPrintJobChange(completed);
            applyPrintJobsChange(queuedJobs.records.filter((job) => job.id !== nextJob.id));
            applyErrorMessage('');
          });
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unable to dispatch runtime print job';
          const refreshedStatus = await hardwareAdapterRef.current.getStatus().catch(() => null);
          if (!isCancelled && refreshedStatus) {
            startTransition(() => {
              setHardwareStatus(refreshedStatus);
            });
          }

          if (shouldLeavePrintJobQueued(message)) {
            if (!isCancelled) {
              startTransition(() => {
                setHardwareError(message);
                applyErrorMessage(message);
              });
            }
            return;
          }

          try {
            const failed = await storeControlPlaneClient.completeRuntimePrintJob(
              args.accessToken,
              args.tenantId,
              args.branchId,
              args.selectedRuntimeDeviceId,
              nextJob.id,
              { status: 'FAILED', failure_reason: message },
            );
            if (isCancelled) {
              return;
            }
            startTransition(() => {
              applyLatestPrintJobChange(failed);
              applyPrintJobsChange(queuedJobs.records.filter((job) => job.id !== nextJob.id));
              setHardwareError(message);
              applyErrorMessage(message);
            });
          } catch {
            if (!isCancelled) {
              startTransition(() => {
                setHardwareError(message);
                applyErrorMessage(message);
              });
            }
          }
        }
      } finally {
        printDispatchInFlightRef.current = false;
      }
    };

    void runPoll();
    const interval = window.setInterval(() => {
      void runPoll();
    }, args.pollIntervalMs ?? HARDWARE_POLL_INTERVAL_MS);

    return () => {
      isCancelled = true;
      window.clearInterval(interval);
    };
  }, [
    args.accessToken,
    args.branchId,
    args.isLocalUnlocked,
    args.isSessionLive,
    args.runtimeShellKind,
    args.selectedRuntimeDeviceId,
    args.tenantId,
    applyErrorMessage,
    applyLatestPrintJobChange,
    applyPrintJobsChange,
  ]);

  async function savePrinterProfile(profile: StoreRuntimeHardwareProfileInput) {
    const nextStatus = await hardwareAdapterRef.current.saveProfile(profile);
    startTransition(() => {
      setHardwareStatus(nextStatus);
      setHardwareError(null);
    });
    return nextStatus;
  }

  async function assignReceiptPrinter(printerName: string | null) {
    return savePrinterProfile({
      receipt_printer_name: printerName,
      label_printer_name: hardwareStatus?.profile.label_printer_name ?? null,
    });
  }

  async function assignLabelPrinter(printerName: string | null) {
    return savePrinterProfile({
      receipt_printer_name: hardwareStatus?.profile.receipt_printer_name ?? null,
      label_printer_name: printerName,
    });
  }

  return {
    hardwareError,
    hardwareStatus,
    refreshHardwareStatus,
    assignLabelPrinter,
    assignReceiptPrinter,
  };
}
