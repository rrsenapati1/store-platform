import type {
  ControlPlaneActor,
  ControlPlaneBatchExpiryReport,
  ControlPlaneBatchExpiryWriteOff,
  ControlPlaneBarcodeScanLookup,
  ControlPlaneBranchCatalogItem,
  ControlPlaneBranchRecord,
  ControlPlaneBranchCustomerReport,
  ControlPlaneCustomerDirectoryRecord,
  ControlPlaneCustomerHistoryResponse,
  ControlPlaneDeviceRecord,
  ControlPlaneExchange,
  ControlPlaneInventorySnapshotRecord,
  ControlPlaneOfflineSaleReplayRequest,
  ControlPlaneOfflineSaleReplayResponse,
  ControlPlanePrintJob,
  ControlPlaneRuntimeDeviceClaimResolution,
  ControlPlaneRuntimeHubBootstrap,
  ControlPlaneRuntimeHeartbeat,
  ControlPlaneSale,
  ControlPlaneSaleRecord,
  ControlPlaneSaleReturn,
  ControlPlaneSession,
  ControlPlaneStoreDesktopActivationSession,
  ControlPlaneSupplierAgingReport,
  ControlPlaneSupplierDueScheduleReport,
  ControlPlaneSupplierEscalationReport,
  ControlPlaneSupplierExceptionReport,
  ControlPlaneSupplierPaymentActivityReport,
  ControlPlaneSupplierPayablesReport,
  ControlPlaneSupplierPerformanceReport,
  ControlPlaneSupplierSettlementBlockerReport,
  ControlPlaneSupplierSettlementReport,
  ControlPlaneSupplierStatementReport,
  ControlPlaneSyncConflictRecord,
  ControlPlaneSyncEnvelopeRecord,
  ControlPlaneSyncSpokeRecord,
  ControlPlaneSyncStatus,
  ControlPlaneTenant,
  ControlPlaneVendorDisputeBoard,
} from '@store/types';
import { normalizeScannedBarcode } from '@store/barcode';
import { resolveControlPlaneRequestUrl } from './controlPlaneOrigin';

export class ControlPlaneRequestError extends Error {
  readonly status: number;
  readonly detail: string | null;

  constructor(status: number, detail?: string | null) {
    super(detail || `Control-plane request failed with status ${status}`);
    this.name = 'ControlPlaneRequestError';
    this.status = status;
    this.detail = detail ?? null;
  }
}

async function request<T>(path: string, init?: RequestInit, accessToken?: string): Promise<T> {
  const response = await fetch(await resolveControlPlaneRequestUrl(path), {
    ...init,
    headers: {
      'content-type': 'application/json',
      ...(accessToken ? { authorization: `Bearer ${accessToken}` } : {}),
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail: string | null = null;
    try {
      const payload = await response.json() as { detail?: unknown };
      if (typeof payload.detail === 'string') {
        detail = payload.detail;
      }
    } catch {
      detail = null;
    }
    throw new ControlPlaneRequestError(response.status, detail);
  }

  return (await response.json()) as T;
}

async function requestWithHeaders<T>(path: string, headers: Record<string, string>, init?: RequestInit): Promise<T> {
  const response = await fetch(await resolveControlPlaneRequestUrl(path), {
    ...init,
    headers: {
      'content-type': 'application/json',
      ...headers,
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let detail: string | null = null;
    try {
      const payload = await response.json() as { detail?: unknown };
      if (typeof payload.detail === 'string') {
        detail = payload.detail;
      }
    } catch {
      detail = null;
    }
    throw new ControlPlaneRequestError(response.status, detail);
  }

  return (await response.json()) as T;
}

export const storeControlPlaneClient = {
  exchangeSession(token: string) {
    return request<ControlPlaneSession>('/v1/auth/oidc/exchange', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  },
  activateStoreDesktopSession(installationId: string, activationCode: string) {
    return request<ControlPlaneStoreDesktopActivationSession>('/v1/auth/store-desktop/activate', {
      method: 'POST',
      body: JSON.stringify({
        installation_id: installationId,
        activation_code: activationCode,
      }),
    });
  },
  unlockStoreDesktopSession(installationId: string, localAuthToken: string) {
    return request<ControlPlaneStoreDesktopActivationSession>('/v1/auth/store-desktop/unlock', {
      method: 'POST',
      body: JSON.stringify({
        installation_id: installationId,
        local_auth_token: localAuthToken,
      }),
    });
  },
  replayOfflineSale(deviceId: string, deviceSecret: string, payload: ControlPlaneOfflineSaleReplayRequest) {
    return requestWithHeaders<ControlPlaneOfflineSaleReplayResponse>(
      '/v1/sync/offline-sales/replay',
      {
        'x-store-device-id': deviceId,
        'x-store-device-secret': deviceSecret,
      },
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
    );
  },
  refreshSession(accessToken: string) {
    return request<ControlPlaneSession>(
      '/v1/auth/refresh',
      {
        method: 'POST',
      },
      accessToken,
    );
  },
  signOut(accessToken: string) {
    return request<{ status: string }>(
      '/v1/auth/sign-out',
      {
        method: 'POST',
      },
      accessToken,
    );
  },
  getActor(accessToken: string) {
    return request<ControlPlaneActor>('/v1/auth/me', undefined, accessToken);
  },
  getTenantSummary(accessToken: string, tenantId: string) {
    return request<ControlPlaneTenant>(`/v1/tenants/${tenantId}`, undefined, accessToken);
  },
  listBranches(accessToken: string, tenantId: string) {
    return request<{ records: ControlPlaneBranchRecord[] }>(`/v1/tenants/${tenantId}/branches`, undefined, accessToken);
  },
  listBranchCatalogItems(accessToken: string, tenantId: string, branchId: string) {
    return request<{ records: ControlPlaneBranchCatalogItem[] }>(
      `/v1/tenants/${tenantId}/branches/${branchId}/catalog-items`,
      undefined,
      accessToken,
    );
  },
  lookupCatalogScan(accessToken: string, tenantId: string, branchId: string, barcode: string) {
    const normalizedBarcode = normalizeScannedBarcode(barcode);
    return request<ControlPlaneBarcodeScanLookup>(
      `/v1/tenants/${tenantId}/branches/${branchId}/catalog-scan/${encodeURIComponent(normalizedBarcode)}`,
      undefined,
      accessToken,
    );
  },
  listInventorySnapshot(accessToken: string, tenantId: string, branchId: string) {
    return request<{ records: ControlPlaneInventorySnapshotRecord[] }>(
      `/v1/tenants/${tenantId}/branches/${branchId}/inventory-snapshot`,
      undefined,
      accessToken,
    );
  },
  getBatchExpiryReport(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneBatchExpiryReport>(
      `/v1/tenants/${tenantId}/branches/${branchId}/batch-expiry-report`,
      undefined,
      accessToken,
    );
  },
  getSupplierPayablesReport(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneSupplierPayablesReport>(
      `/v1/tenants/${tenantId}/branches/${branchId}/supplier-payables-report`,
      undefined,
      accessToken,
    );
  },
  getSupplierAgingReport(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneSupplierAgingReport>(
      `/v1/tenants/${tenantId}/branches/${branchId}/supplier-aging-report`,
      undefined,
      accessToken,
    );
  },
  getSupplierStatements(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneSupplierStatementReport>(
      `/v1/tenants/${tenantId}/branches/${branchId}/supplier-statements`,
      undefined,
      accessToken,
    );
  },
  getSupplierDueSchedule(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneSupplierDueScheduleReport>(
      `/v1/tenants/${tenantId}/branches/${branchId}/supplier-due-schedule`,
      undefined,
      accessToken,
    );
  },
  getVendorDisputeBoard(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneVendorDisputeBoard>(
      `/v1/tenants/${tenantId}/branches/${branchId}/vendor-dispute-board`,
      undefined,
      accessToken,
    );
  },
  getSupplierExceptionReport(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneSupplierExceptionReport>(
      `/v1/tenants/${tenantId}/branches/${branchId}/supplier-exception-report`,
      undefined,
      accessToken,
    );
  },
  getSupplierSettlementReport(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneSupplierSettlementReport>(
      `/v1/tenants/${tenantId}/branches/${branchId}/supplier-settlement-report`,
      undefined,
      accessToken,
    );
  },
  getSupplierSettlementBlockers(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneSupplierSettlementBlockerReport>(
      `/v1/tenants/${tenantId}/branches/${branchId}/supplier-settlement-blockers`,
      undefined,
      accessToken,
    );
  },
  getSupplierEscalationReport(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneSupplierEscalationReport>(
      `/v1/tenants/${tenantId}/branches/${branchId}/supplier-escalation-report`,
      undefined,
      accessToken,
    );
  },
  getSupplierPerformanceReport(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneSupplierPerformanceReport>(
      `/v1/tenants/${tenantId}/branches/${branchId}/supplier-performance-report`,
      undefined,
      accessToken,
    );
  },
  getSupplierPaymentActivity(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneSupplierPaymentActivityReport>(
      `/v1/tenants/${tenantId}/branches/${branchId}/supplier-payment-activity`,
      undefined,
      accessToken,
    );
  },
  createBatchExpiryWriteOff(
    accessToken: string,
    tenantId: string,
    branchId: string,
    batchLotId: string,
    payload: { quantity: number; reason: string },
  ) {
    return request<ControlPlaneBatchExpiryWriteOff>(
      `/v1/tenants/${tenantId}/branches/${branchId}/batch-lots/${batchLotId}/expiry-write-offs`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  listSales(accessToken: string, tenantId: string, branchId: string) {
    return request<{ records: ControlPlaneSaleRecord[] }>(`/v1/tenants/${tenantId}/branches/${branchId}/sales`, undefined, accessToken);
  },
  listCustomers(accessToken: string, tenantId: string, query?: string) {
    const queryParam = query ? `?query=${encodeURIComponent(query)}` : '';
    return request<{ records: ControlPlaneCustomerDirectoryRecord[] }>(
      `/v1/tenants/${tenantId}/customers${queryParam}`,
      undefined,
      accessToken,
    );
  },
  getCustomerHistory(accessToken: string, tenantId: string, customerId: string) {
    return request<ControlPlaneCustomerHistoryResponse>(
      `/v1/tenants/${tenantId}/customers/${customerId}/history`,
      undefined,
      accessToken,
    );
  },
  getBranchCustomerReport(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneBranchCustomerReport>(
      `/v1/tenants/${tenantId}/branches/${branchId}/customer-report`,
      undefined,
      accessToken,
    );
  },
  getRuntimeSyncStatus(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneSyncStatus>(
      `/v1/tenants/${tenantId}/branches/${branchId}/runtime/sync-status`,
      undefined,
      accessToken,
    );
  },
  listRuntimeSyncConflicts(accessToken: string, tenantId: string, branchId: string) {
    return request<{ records: ControlPlaneSyncConflictRecord[] }>(
      `/v1/tenants/${tenantId}/branches/${branchId}/runtime/sync-conflicts`,
      undefined,
      accessToken,
    );
  },
  listRuntimeSyncSpokes(accessToken: string, tenantId: string, branchId: string) {
    return request<{ records: ControlPlaneSyncSpokeRecord[] }>(
      `/v1/tenants/${tenantId}/branches/${branchId}/runtime/sync-spokes`,
      undefined,
      accessToken,
    );
  },
  listRuntimeSyncEnvelopes(accessToken: string, tenantId: string, branchId: string) {
    return request<{ records: ControlPlaneSyncEnvelopeRecord[] }>(
      `/v1/tenants/${tenantId}/branches/${branchId}/runtime/sync-envelopes`,
      undefined,
      accessToken,
    );
  },
  listRuntimeDevices(accessToken: string, tenantId: string, branchId: string) {
    return request<{ records: ControlPlaneDeviceRecord[] }>(
      `/v1/tenants/${tenantId}/branches/${branchId}/runtime/devices`,
      undefined,
      accessToken,
    );
  },
  resolveRuntimeDeviceClaim(
    accessToken: string,
    tenantId: string,
    branchId: string,
    payload: {
      installation_id: string;
      runtime_kind: string;
      hostname?: string | null;
      operating_system?: string | null;
      architecture?: string | null;
      app_version?: string | null;
    },
  ) {
    return request<ControlPlaneRuntimeDeviceClaimResolution>(
      `/v1/tenants/${tenantId}/branches/${branchId}/runtime/device-claim`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  bootstrapRuntimeHubIdentity(accessToken: string, tenantId: string, branchId: string, installationId: string) {
    return request<ControlPlaneRuntimeHubBootstrap>(
      `/v1/tenants/${tenantId}/branches/${branchId}/runtime/hub-bootstrap`,
      {
        method: 'POST',
        body: JSON.stringify({
          installation_id: installationId,
        }),
      },
      accessToken,
    );
  },
  createSale(
    accessToken: string,
    tenantId: string,
    branchId: string,
    payload: {
      customer_name: string;
      customer_gstin?: string | null;
      payment_method: string;
      lines: Array<{ product_id: string; quantity: number }>;
    },
  ) {
    return request<ControlPlaneSale>(
      `/v1/tenants/${tenantId}/branches/${branchId}/sales`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  queueSaleInvoicePrintJob(
    accessToken: string,
    tenantId: string,
    branchId: string,
    saleId: string,
    payload: { device_id: string; copies: number },
  ) {
    return request<ControlPlanePrintJob>(
      `/v1/tenants/${tenantId}/branches/${branchId}/runtime/print-jobs/sales/${saleId}`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  createSaleReturn(
    accessToken: string,
    tenantId: string,
    branchId: string,
    saleId: string,
    payload: {
      refund_amount: number;
      refund_method: string;
      lines: Array<{ product_id: string; quantity: number }>;
    },
  ) {
    return request<ControlPlaneSaleReturn>(
      `/v1/tenants/${tenantId}/branches/${branchId}/sales/${saleId}/returns`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  queueSaleReturnPrintJob(
    accessToken: string,
    tenantId: string,
    branchId: string,
    saleReturnId: string,
    payload: { device_id: string; copies: number },
  ) {
    return request<ControlPlanePrintJob>(
      `/v1/tenants/${tenantId}/branches/${branchId}/runtime/print-jobs/sale-returns/${saleReturnId}`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  createExchange(
    accessToken: string,
    tenantId: string,
    branchId: string,
    saleId: string,
    payload: {
      settlement_method: string;
      return_lines: Array<{ product_id: string; quantity: number }>;
      replacement_lines: Array<{ product_id: string; quantity: number }>;
    },
  ) {
    return request<ControlPlaneExchange>(
      `/v1/tenants/${tenantId}/branches/${branchId}/sales/${saleId}/exchanges`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  heartbeatRuntimeDevice(accessToken: string, tenantId: string, branchId: string, deviceId: string) {
    return request<ControlPlaneRuntimeHeartbeat>(
      `/v1/tenants/${tenantId}/branches/${branchId}/runtime/devices/${deviceId}/heartbeat`,
      {
        method: 'POST',
      },
      accessToken,
    );
  },
  listRuntimePrintJobs(accessToken: string, tenantId: string, branchId: string, deviceId: string) {
    return request<{ records: ControlPlanePrintJob[] }>(
      `/v1/tenants/${tenantId}/branches/${branchId}/runtime/devices/${deviceId}/print-jobs`,
      undefined,
      accessToken,
    );
  },
  completeRuntimePrintJob(
    accessToken: string,
    tenantId: string,
    branchId: string,
    deviceId: string,
    printJobId: string,
    payload: { status: string; failure_reason?: string | null },
  ) {
    return request<ControlPlanePrintJob>(
      `/v1/tenants/${tenantId}/branches/${branchId}/runtime/devices/${deviceId}/print-jobs/${printJobId}/complete`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
};
