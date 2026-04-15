import { useEffect, useEffectEvent, useRef, useState } from 'react';
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
  const isMountedRef = useRef(false);
  const [hardwareStatus, setHardwareStatus] = useState<StoreRuntimeHardwareStatus | null>(null);
  const [hardwareError, setHardwareError] = useState<string | null>(null);
  const printDispatchInFlightRef = useRef(false);

  const applyPrintJobsChange = useEffectEvent(args.onPrintJobsChange);
  const applyLatestPrintJobChange = useEffectEvent(args.onLatestPrintJobChange);
  const applyErrorMessage = useEffectEvent(args.onErrorMessage);
  const applyStateTransition = useEffectEvent((callback: () => void) => {
    if (!isMountedRef.current) {
      return;
    }
    callback();
  });

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const refreshHardwareStatus = useEffectEvent(async () => {
    const nextStatus = await hardwareAdapterRef.current.getStatus();
    applyStateTransition(() => {
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
        applyStateTransition(() => {
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
        applyStateTransition(() => {
          setHardwareStatus(nextHardwareStatus);
          setHardwareError(null);
        });
        if (nextHardwareStatus.bridge_state !== 'ready') {
          return;
        }

        const queuedJobs = await storeControlPlaneClient.listRuntimePrintJobs(
          args.accessToken,
          args.tenantId,
          args.branchId,
          args.selectedRuntimeDeviceId,
        );
        if (isCancelled) {
          return;
        }
        applyStateTransition(() => {
          applyPrintJobsChange(queuedJobs.records);
        });

        const nextJob = queuedJobs.records[0];
        if (!nextJob) {
          return;
        }

        try {
          const dispatchStatus = await hardwareAdapterRef.current.dispatchPrintJob(toHardwarePrintJob(nextJob));
          if (isCancelled) {
            return;
          }
          applyStateTransition(() => {
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
          applyStateTransition(() => {
            applyLatestPrintJobChange(completed);
            applyPrintJobsChange(queuedJobs.records.filter((job) => job.id !== nextJob.id));
            applyErrorMessage('');
          });
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unable to dispatch runtime print job';
          const refreshedStatus = await hardwareAdapterRef.current.getStatus().catch(() => null);
          if (!isCancelled && refreshedStatus) {
            applyStateTransition(() => {
              setHardwareStatus(refreshedStatus);
            });
          }

          if (shouldLeavePrintJobQueued(message)) {
            if (!isCancelled) {
              applyStateTransition(() => {
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
            applyStateTransition(() => {
              applyLatestPrintJobChange(failed);
              applyPrintJobsChange(queuedJobs.records.filter((job) => job.id !== nextJob.id));
              setHardwareError(message);
              applyErrorMessage(message);
            });
          } catch {
            if (!isCancelled) {
              applyStateTransition(() => {
                setHardwareError(message);
                applyErrorMessage(message);
              });
            }
          }
        }
      } catch (error) {
        if (!isCancelled) {
          const message = error instanceof Error ? error.message : 'Unable to load runtime hardware status';
          applyStateTransition(() => {
            setHardwareError(message);
            applyErrorMessage(message);
          });
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
    applyStateTransition,
  ]);

  async function savePrinterProfile(profile: StoreRuntimeHardwareProfileInput) {
    const nextStatus = await hardwareAdapterRef.current.saveProfile(profile);
    applyStateTransition(() => {
      setHardwareStatus(nextStatus);
      setHardwareError(null);
    });
    return nextStatus;
  }

  async function assignReceiptPrinter(printerName: string | null) {
    return savePrinterProfile({
      receipt_printer_name: printerName,
      label_printer_name: hardwareStatus?.profile.label_printer_name ?? null,
      cash_drawer_printer_name: hardwareStatus?.profile.cash_drawer_printer_name ?? null,
      preferred_scale_id: hardwareStatus?.profile.preferred_scale_id ?? null,
      preferred_scanner_id: hardwareStatus?.profile.preferred_scanner_id ?? null,
    });
  }

  async function assignLabelPrinter(printerName: string | null) {
    return savePrinterProfile({
      receipt_printer_name: hardwareStatus?.profile.receipt_printer_name ?? null,
      label_printer_name: printerName,
      cash_drawer_printer_name: hardwareStatus?.profile.cash_drawer_printer_name ?? null,
      preferred_scale_id: hardwareStatus?.profile.preferred_scale_id ?? null,
      preferred_scanner_id: hardwareStatus?.profile.preferred_scanner_id ?? null,
    });
  }

  async function assignCashDrawerPrinter(printerName: string | null) {
    return savePrinterProfile({
      receipt_printer_name: hardwareStatus?.profile.receipt_printer_name ?? null,
      label_printer_name: hardwareStatus?.profile.label_printer_name ?? null,
      cash_drawer_printer_name: printerName,
      preferred_scale_id: hardwareStatus?.profile.preferred_scale_id ?? null,
      preferred_scanner_id: hardwareStatus?.profile.preferred_scanner_id ?? null,
    });
  }

  async function assignPreferredScale(scaleId: string | null) {
    return savePrinterProfile({
      receipt_printer_name: hardwareStatus?.profile.receipt_printer_name ?? null,
      label_printer_name: hardwareStatus?.profile.label_printer_name ?? null,
      cash_drawer_printer_name: hardwareStatus?.profile.cash_drawer_printer_name ?? null,
      preferred_scale_id: scaleId,
      preferred_scanner_id: hardwareStatus?.profile.preferred_scanner_id ?? null,
    });
  }

  async function assignPreferredScanner(scannerId: string | null) {
    return savePrinterProfile({
      receipt_printer_name: hardwareStatus?.profile.receipt_printer_name ?? null,
      label_printer_name: hardwareStatus?.profile.label_printer_name ?? null,
      cash_drawer_printer_name: hardwareStatus?.profile.cash_drawer_printer_name ?? null,
      preferred_scale_id: hardwareStatus?.profile.preferred_scale_id ?? null,
      preferred_scanner_id: scannerId,
    });
  }

  async function openCashDrawer() {
    try {
      const nextStatus = await hardwareAdapterRef.current.openCashDrawer();
      applyStateTransition(() => {
        setHardwareStatus(nextStatus);
        setHardwareError(null);
      });
      return nextStatus;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to open the assigned cash drawer';
      try {
        const refreshedStatus = await hardwareAdapterRef.current.getStatus();
        applyStateTransition(() => {
          setHardwareStatus(refreshedStatus);
          setHardwareError(message);
        });
      } catch {
        applyStateTransition(() => {
          setHardwareError(message);
        });
      }
      throw error instanceof Error ? error : new Error(message);
    }
  }

  async function readScaleWeight() {
    try {
      const nextStatus = await hardwareAdapterRef.current.readScaleWeight();
      applyStateTransition(() => {
        setHardwareStatus(nextStatus);
        setHardwareError(null);
      });
      return nextStatus;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to read from the assigned weighing scale';
      try {
        const refreshedStatus = await hardwareAdapterRef.current.getStatus();
        applyStateTransition(() => {
          setHardwareStatus(refreshedStatus);
          setHardwareError(message);
        });
      } catch {
        applyStateTransition(() => {
          setHardwareError(message);
        });
      }
      throw error instanceof Error ? error : new Error(message);
    }
  }

  async function recordScannerActivity(activity: {
    barcode_preview: string;
    scanner_transport: 'keyboard_wedge' | 'usb_hid' | 'bluetooth_hid' | 'unknown' | null;
  }) {
    const nextStatus = await hardwareAdapterRef.current.recordScannerActivity(activity);
    applyStateTransition(() => {
      setHardwareStatus(nextStatus);
      setHardwareError(null);
    });
  }

  return {
    hardwareError,
    hardwareStatus,
    refreshHardwareStatus,
    assignLabelPrinter,
    assignCashDrawerPrinter,
    assignPreferredScale,
    assignReceiptPrinter,
    assignPreferredScanner,
    openCashDrawer,
    readScaleWeight,
    recordScannerActivity,
  };
}
