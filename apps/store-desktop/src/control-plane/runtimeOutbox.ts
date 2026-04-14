import type { ControlPlanePrintJob, ControlPlaneRuntimeHeartbeat } from '@store/types';
import type {
  StoreRuntimePendingCreditNotePrintMutation,
  StoreRuntimePendingHeartbeatMutation,
  StoreRuntimePendingMutation,
  StoreRuntimePendingSalesInvoicePrintMutation,
} from '../runtime-cache/storeRuntimeCache';
import { ControlPlaneRequestError, storeControlPlaneClient } from './client';

type ReplayPendingRuntimeMutationsArgs = {
  accessToken: string;
  mutations: StoreRuntimePendingMutation[];
};

export type ReplayPendingRuntimeMutationsResult = {
  remainingMutations: StoreRuntimePendingMutation[];
  latestHeartbeat: ControlPlaneRuntimeHeartbeat | null;
  latestPrintJob: ControlPlanePrintJob | null;
  refreshPrintQueueDeviceIds: string[];
};

function buildPendingMutationId() {
  const randomPart = globalThis.crypto?.randomUUID?.() ?? Math.random().toString(16).slice(2);
  return `runtime-pending-${Date.now()}-${randomPart}`;
}

function buildPendingMutationBase(args: {
  tenantId: string;
  branchId: string;
  deviceId: string;
}) {
  return {
    id: buildPendingMutationId(),
    tenant_id: args.tenantId,
    branch_id: args.branchId,
    device_id: args.deviceId,
    status: 'PENDING' as const,
    created_at: new Date().toISOString(),
  };
}

export function shouldQueueRuntimeOutboxMutation(error: unknown) {
  return !(error instanceof ControlPlaneRequestError) || error.status >= 500;
}

export function createPendingHeartbeatMutation(args: {
  tenantId: string;
  branchId: string;
  deviceId: string;
}): StoreRuntimePendingHeartbeatMutation {
  return {
    ...buildPendingMutationBase(args),
    mutation_type: 'HEARTBEAT',
  };
}

export function createPendingSalesInvoicePrintMutation(args: {
  tenantId: string;
  branchId: string;
  deviceId: string;
  saleId: string;
  documentNumber: string;
  copies: number;
}): StoreRuntimePendingSalesInvoicePrintMutation {
  return {
    ...buildPendingMutationBase(args),
    mutation_type: 'PRINT_SALES_INVOICE',
    reference_id: args.saleId,
    document_number: args.documentNumber,
    copies: args.copies,
  };
}

export function createPendingCreditNotePrintMutation(args: {
  tenantId: string;
  branchId: string;
  deviceId: string;
  saleReturnId: string;
  documentNumber: string;
  copies: number;
}): StoreRuntimePendingCreditNotePrintMutation {
  return {
    ...buildPendingMutationBase(args),
    mutation_type: 'PRINT_CREDIT_NOTE',
    reference_id: args.saleReturnId,
    document_number: args.documentNumber,
    copies: args.copies,
  };
}

export function describePendingRuntimeMutation(mutation: StoreRuntimePendingMutation) {
  switch (mutation.mutation_type) {
    case 'HEARTBEAT':
      return `Heartbeat :: ${mutation.device_id}`;
    case 'PRINT_SALES_INVOICE':
      return `Invoice print :: ${mutation.document_number}`;
    case 'PRINT_CREDIT_NOTE':
      return `Credit note print :: ${mutation.document_number}`;
  }
}

export async function replayPendingRuntimeMutations({
  accessToken,
  mutations,
}: ReplayPendingRuntimeMutationsArgs): Promise<ReplayPendingRuntimeMutationsResult> {
  const remainingMutations: StoreRuntimePendingMutation[] = [];
  const refreshPrintQueueDeviceIds = new Set<string>();
  let latestHeartbeat: ControlPlaneRuntimeHeartbeat | null = null;
  let latestPrintJob: ControlPlanePrintJob | null = null;

  for (const mutation of mutations) {
    try {
      switch (mutation.mutation_type) {
        case 'HEARTBEAT':
          latestHeartbeat = await storeControlPlaneClient.heartbeatRuntimeDevice(
            accessToken,
            mutation.tenant_id,
            mutation.branch_id,
            mutation.device_id,
          );
          break;
        case 'PRINT_SALES_INVOICE':
          latestPrintJob = await storeControlPlaneClient.queueSaleInvoicePrintJob(
            accessToken,
            mutation.tenant_id,
            mutation.branch_id,
            mutation.reference_id,
            {
              device_id: mutation.device_id,
              copies: mutation.copies,
            },
          );
          refreshPrintQueueDeviceIds.add(mutation.device_id);
          break;
        case 'PRINT_CREDIT_NOTE':
          latestPrintJob = await storeControlPlaneClient.queueSaleReturnPrintJob(
            accessToken,
            mutation.tenant_id,
            mutation.branch_id,
            mutation.reference_id,
            {
              device_id: mutation.device_id,
              copies: mutation.copies,
            },
          );
          refreshPrintQueueDeviceIds.add(mutation.device_id);
          break;
      }
    } catch (error) {
      if (shouldQueueRuntimeOutboxMutation(error)) {
        remainingMutations.push(mutation);
      }
    }
  }

  return {
    remainingMutations,
    latestHeartbeat,
    latestPrintJob,
    refreshPrintQueueDeviceIds: Array.from(refreshPrintQueueDeviceIds),
  };
}
