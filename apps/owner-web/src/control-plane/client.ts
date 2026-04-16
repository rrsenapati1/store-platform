import type {
  ControlPlaneActor,
  ControlPlaneAuditRecord,
  ControlPlaneBatchExpiryReport,
  ControlPlaneBatchExpiryBoard,
  ControlPlaneBatchExpiryReviewApproval,
  ControlPlaneBatchExpiryReviewSession,
  ControlPlaneBatchExpiryWriteOff,
  ControlPlaneGoodsReceiptBatchLotIntake,
  ControlPlaneBarcodeAllocation,
  ControlPlaneBarcodeLabelPreview,
  ControlPlaneBranchCatalogItem,
  ControlPlaneBranch,
  ControlPlaneBranchRecord,
  ControlPlaneBranchCustomerReport,
  ControlPlaneCatalogProduct,
  ControlPlaneCatalogProductRecord,
  ControlPlaneCustomerDirectoryRecord,
  ControlPlaneCustomerProfile,
  ControlPlaneCustomerHistoryResponse,
  ControlPlaneComplianceProviderProfile,
  ControlPlaneDeviceClaimApproval,
  ControlPlaneDeviceClaimRecord,
  ControlPlaneDeviceRecord,
  ControlPlaneDeviceRegistration,
  ControlPlaneStoreDesktopActivation,
  ControlPlaneGstExportJob,
  ControlPlaneGstExportReport,
  ControlPlaneGoodsReceipt,
  ControlPlaneGoodsReceiptRecord,
  ControlPlaneInventoryLedgerRecord,
  ControlPlaneInventorySnapshotRecord,
  ControlPlaneMembership,
  ControlPlanePrintJob,
  ControlPlanePurchaseApprovalReport,
  ControlPlanePurchaseInvoice,
  ControlPlanePurchaseInvoiceRecord,
  ControlPlanePurchaseOrder,
  ControlPlanePurchaseOrderRecord,
  ControlPlaneReplenishmentBoard,
  ControlPlaneRestockBoard,
  ControlPlaneRestockTask,
  ControlPlaneReceivingBoard,
  ControlPlaneSaleRecord,
  ControlPlaneSubscriptionBootstrap,
  ControlPlaneSupplierPayablesReport,
  ControlPlaneSupplierPayment,
  ControlPlaneSupplierReturn,
  ControlPlaneSaleReturn,
  ControlPlaneSaleReturnRecord,
  ControlPlaneSession,
  ControlPlaneStockAdjustment,
  ControlPlaneStockCountApproval,
  ControlPlaneStockCountBoard,
  ControlPlaneStockCount,
  ControlPlaneStockCountReviewSession,
  ControlPlaneStaffProfile,
  ControlPlaneStaffProfileRecord,
  ControlPlaneSupplier,
  ControlPlaneSupplierAgingReport,
  ControlPlaneSupplierDueScheduleReport,
  ControlPlaneSupplierEscalationReport,
  ControlPlaneSupplierExceptionReport,
  ControlPlaneSupplierPaymentActivityReport,
  ControlPlaneSyncConflictRecord,
  ControlPlaneSyncEnvelopeRecord,
  ControlPlaneSyncStatus,
  ControlPlaneSupplierPerformanceReport,
  ControlPlaneSupplierRecord,
  ControlPlaneSupplierSettlementBlockerReport,
  ControlPlaneSupplierSettlementReport,
  ControlPlaneSupplierStatementReport,
  ControlPlaneTenant,
  ControlPlaneTenantLifecycleSummary,
  ControlPlaneTransfer,
  ControlPlaneVendorDisputeBoard,
  ControlPlaneTransferBoard,
} from '@store/types';

async function request<T>(path: string, init?: RequestInit, accessToken?: string): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      'content-type': 'application/json',
      ...(accessToken ? { authorization: `Bearer ${accessToken}` } : {}),
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error(`Control-plane request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export const ownerControlPlaneClient = {
  exchangeSession(token: string) {
    return request<ControlPlaneSession>('/v1/auth/oidc/exchange', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  },
  getActor(accessToken: string) {
    return request<ControlPlaneActor>('/v1/auth/me', undefined, accessToken);
  },
  getTenantSummary(accessToken: string, tenantId: string) {
    return request<ControlPlaneTenant>(`/v1/tenants/${tenantId}`, undefined, accessToken);
  },
  getTenantBillingLifecycle(accessToken: string, tenantId: string) {
    return request<ControlPlaneTenantLifecycleSummary>(`/v1/tenants/${tenantId}/billing/lifecycle`, undefined, accessToken);
  },
  bootstrapTenantSubscription(accessToken: string, tenantId: string, payload: { provider_name: string }) {
    return request<ControlPlaneSubscriptionBootstrap>(
      `/v1/tenants/${tenantId}/billing/subscription-bootstrap`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  listBranches(accessToken: string, tenantId: string) {
    return request<{ records: ControlPlaneBranchRecord[] }>(`/v1/tenants/${tenantId}/branches`, undefined, accessToken);
  },
  listAuditEvents(accessToken: string, tenantId: string) {
    return request<{ records: ControlPlaneAuditRecord[] }>(`/v1/tenants/${tenantId}/audit-events`, undefined, accessToken);
  },
  listStaffProfiles(accessToken: string, tenantId: string) {
    return request<{ records: ControlPlaneStaffProfileRecord[] }>(`/v1/tenants/${tenantId}/staff-profiles`, undefined, accessToken);
  },
  listCatalogProducts(accessToken: string, tenantId: string) {
    return request<{ records: ControlPlaneCatalogProductRecord[] }>(`/v1/tenants/${tenantId}/catalog/products`, undefined, accessToken);
  },
  allocateCatalogProductBarcode(
    accessToken: string,
    tenantId: string,
    productId: string,
    payload: { barcode?: string | null },
  ) {
    return request<ControlPlaneBarcodeAllocation>(
      `/v1/tenants/${tenantId}/catalog/products/${productId}/barcode-allocation`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  getBarcodeLabelPreview(accessToken: string, tenantId: string, branchId: string, productId: string) {
    return request<ControlPlaneBarcodeLabelPreview>(
      `/v1/tenants/${tenantId}/branches/${branchId}/barcode-label-preview/${productId}`,
      undefined,
      accessToken,
    );
  },
  queueBarcodeLabelPrintJob(
    accessToken: string,
    tenantId: string,
    branchId: string,
    productId: string,
    payload: { device_id: string; copies: number },
  ) {
    return request<ControlPlanePrintJob>(
      `/v1/tenants/${tenantId}/branches/${branchId}/runtime/print-jobs/barcode-labels/${productId}`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  listSuppliers(accessToken: string, tenantId: string) {
    return request<{ records: ControlPlaneSupplierRecord[] }>(`/v1/tenants/${tenantId}/suppliers`, undefined, accessToken);
  },
  createBranch(
    accessToken: string,
    tenantId: string,
    payload: { name: string; code: string; gstin?: string | null; timezone?: string },
  ) {
    return request<ControlPlaneBranch>(
      `/v1/tenants/${tenantId}/branches`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  createStaffProfile(
    accessToken: string,
    tenantId: string,
    payload: { email: string; full_name: string; phone_number?: string | null; primary_branch_id?: string | null },
  ) {
    return request<ControlPlaneStaffProfile>(
      `/v1/tenants/${tenantId}/staff-profiles`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  createCatalogProduct(
    accessToken: string,
    tenantId: string,
    payload: { name: string; sku_code: string; barcode: string; hsn_sac_code: string; gst_rate: number; selling_price: number },
  ) {
    return request<ControlPlaneCatalogProduct>(
      `/v1/tenants/${tenantId}/catalog/products`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  createSupplier(
    accessToken: string,
    tenantId: string,
    payload: { name: string; gstin?: string | null; payment_terms_days: number },
  ) {
    return request<ControlPlaneSupplier>(
      `/v1/tenants/${tenantId}/suppliers`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  createTenantMembership(
    accessToken: string,
    tenantId: string,
    payload: { email: string; full_name: string; role_name: string },
  ) {
    return request<ControlPlaneMembership>(
      `/v1/tenants/${tenantId}/memberships`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  createBranchMembership(
    accessToken: string,
    tenantId: string,
    branchId: string,
    payload: { email: string; full_name: string; role_name: string },
  ) {
    return request<ControlPlaneMembership>(
      `/v1/tenants/${tenantId}/branches/${branchId}/memberships`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  listBranchCatalogItems(accessToken: string, tenantId: string, branchId: string) {
    return request<{ records: ControlPlaneBranchCatalogItem[] }>(
      `/v1/tenants/${tenantId}/branches/${branchId}/catalog-items`,
      undefined,
      accessToken,
    );
  },
  upsertBranchCatalogItem(
    accessToken: string,
    tenantId: string,
    branchId: string,
    payload: {
      product_id: string;
      selling_price_override?: number | null;
      availability_status: string;
      reorder_point?: number | null;
      target_stock?: number | null;
    },
  ) {
    return request<ControlPlaneBranchCatalogItem>(
      `/v1/tenants/${tenantId}/branches/${branchId}/catalog-items`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  getReplenishmentBoard(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneReplenishmentBoard>(
      `/v1/tenants/${tenantId}/branches/${branchId}/replenishment-board`,
      undefined,
      accessToken,
    );
  },
  getRestockBoard(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneRestockBoard>(
      `/v1/tenants/${tenantId}/branches/${branchId}/restock-board`,
      undefined,
      accessToken,
    );
  },
  createRestockTask(
    accessToken: string,
    tenantId: string,
    branchId: string,
    payload: { product_id: string; requested_quantity: number; source_posture: string; note?: string | null },
  ) {
    return request<ControlPlaneRestockTask>(
      `/v1/tenants/${tenantId}/branches/${branchId}/restock-tasks`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  pickRestockTask(
    accessToken: string,
    tenantId: string,
    branchId: string,
    restockTaskId: string,
    payload: { picked_quantity: number; note?: string | null },
  ) {
    return request<ControlPlaneRestockTask>(
      `/v1/tenants/${tenantId}/branches/${branchId}/restock-tasks/${restockTaskId}/pick`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  completeRestockTask(
    accessToken: string,
    tenantId: string,
    branchId: string,
    restockTaskId: string,
    payload: { completion_note?: string | null },
  ) {
    return request<ControlPlaneRestockTask>(
      `/v1/tenants/${tenantId}/branches/${branchId}/restock-tasks/${restockTaskId}/complete`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  cancelRestockTask(
    accessToken: string,
    tenantId: string,
    branchId: string,
    restockTaskId: string,
    payload: { cancel_note?: string | null },
  ) {
    return request<ControlPlaneRestockTask>(
      `/v1/tenants/${tenantId}/branches/${branchId}/restock-tasks/${restockTaskId}/cancel`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  listPurchaseOrders(accessToken: string, tenantId: string, branchId: string) {
    return request<{ records: ControlPlanePurchaseOrderRecord[] }>(
      `/v1/tenants/${tenantId}/branches/${branchId}/purchase-orders`,
      undefined,
      accessToken,
    );
  },
  createPurchaseOrder(
    accessToken: string,
    tenantId: string,
    branchId: string,
    payload: { supplier_id: string; lines: Array<{ product_id: string; quantity: number; unit_cost: number }> },
  ) {
    return request<ControlPlanePurchaseOrder>(
      `/v1/tenants/${tenantId}/branches/${branchId}/purchase-orders`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  getPurchaseApprovalReport(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlanePurchaseApprovalReport>(
      `/v1/tenants/${tenantId}/branches/${branchId}/purchase-approval-report`,
      undefined,
      accessToken,
    );
  },
  getReceivingBoard(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneReceivingBoard>(
      `/v1/tenants/${tenantId}/branches/${branchId}/receiving-board`,
      undefined,
      accessToken,
    );
  },
  listPurchaseInvoices(accessToken: string, tenantId: string, branchId: string) {
    return request<{ records: ControlPlanePurchaseInvoiceRecord[] }>(
      `/v1/tenants/${tenantId}/branches/${branchId}/purchase-invoices`,
      undefined,
      accessToken,
    );
  },
  createPurchaseInvoice(
    accessToken: string,
    tenantId: string,
    branchId: string,
    payload: { goods_receipt_id: string },
  ) {
    return request<ControlPlanePurchaseInvoice>(
      `/v1/tenants/${tenantId}/branches/${branchId}/purchase-invoices`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  createSupplierReturn(
    accessToken: string,
    tenantId: string,
    branchId: string,
    purchaseInvoiceId: string,
    payload: { lines: Array<{ product_id: string; quantity: number }> },
  ) {
    return request<ControlPlaneSupplierReturn>(
      `/v1/tenants/${tenantId}/branches/${branchId}/purchase-invoices/${purchaseInvoiceId}/supplier-returns`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  createSupplierPayment(
    accessToken: string,
    tenantId: string,
    branchId: string,
    purchaseInvoiceId: string,
    payload: { amount: number; payment_method: string; reference?: string | null },
  ) {
    return request<ControlPlaneSupplierPayment>(
      `/v1/tenants/${tenantId}/branches/${branchId}/purchase-invoices/${purchaseInvoiceId}/supplier-payments`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
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
  createGoodsReceipt(
    accessToken: string,
    tenantId: string,
    branchId: string,
    payload: {
      purchase_order_id: string;
      note?: string | null;
      lines?: Array<{ product_id: string; received_quantity: number; discrepancy_note?: string | null }>;
    },
  ) {
    return request<ControlPlaneGoodsReceipt>(
      `/v1/tenants/${tenantId}/branches/${branchId}/goods-receipts`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  listGoodsReceipts(accessToken: string, tenantId: string, branchId: string) {
    return request<{ records: ControlPlaneGoodsReceiptRecord[] }>(
      `/v1/tenants/${tenantId}/branches/${branchId}/goods-receipts`,
      undefined,
      accessToken,
    );
  },
  createGoodsReceiptBatchLots(
    accessToken: string,
    tenantId: string,
    branchId: string,
    goodsReceiptId: string,
    payload: {
      lots: Array<{ product_id: string; batch_number: string; quantity: number; expiry_date: string }>;
    },
  ) {
    return request<ControlPlaneGoodsReceiptBatchLotIntake>(
      `/v1/tenants/${tenantId}/branches/${branchId}/goods-receipts/${goodsReceiptId}/batch-lots`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
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
  getBatchExpiryBoard(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneBatchExpiryBoard>(
      `/v1/tenants/${tenantId}/branches/${branchId}/batch-expiry-board`,
      undefined,
      accessToken,
    );
  },
  createBatchExpirySession(
    accessToken: string,
    tenantId: string,
    branchId: string,
    payload: { batch_lot_id: string; note?: string | null },
  ) {
    return request<ControlPlaneBatchExpiryReviewSession>(
      `/v1/tenants/${tenantId}/branches/${branchId}/batch-expiry-sessions`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  recordBatchExpirySession(
    accessToken: string,
    tenantId: string,
    branchId: string,
    batchExpirySessionId: string,
    payload: { quantity: number; reason: string },
  ) {
    return request<ControlPlaneBatchExpiryReviewSession>(
      `/v1/tenants/${tenantId}/branches/${branchId}/batch-expiry-sessions/${batchExpirySessionId}/review`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  approveBatchExpirySession(
    accessToken: string,
    tenantId: string,
    branchId: string,
    batchExpirySessionId: string,
    payload: { review_note?: string | null },
  ) {
    return request<ControlPlaneBatchExpiryReviewApproval>(
      `/v1/tenants/${tenantId}/branches/${branchId}/batch-expiry-sessions/${batchExpirySessionId}/approve`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  cancelBatchExpirySession(
    accessToken: string,
    tenantId: string,
    branchId: string,
    batchExpirySessionId: string,
    payload: { review_note?: string | null },
  ) {
    return request<ControlPlaneBatchExpiryReviewSession>(
      `/v1/tenants/${tenantId}/branches/${branchId}/batch-expiry-sessions/${batchExpirySessionId}/cancel`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
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
  listInventoryLedger(accessToken: string, tenantId: string, branchId: string) {
    return request<{ records: ControlPlaneInventoryLedgerRecord[] }>(
      `/v1/tenants/${tenantId}/branches/${branchId}/inventory-ledger`,
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
  listSaleReturns(accessToken: string, tenantId: string, branchId: string) {
    return request<{ records: ControlPlaneSaleReturnRecord[] }>(
      `/v1/tenants/${tenantId}/branches/${branchId}/sale-returns`,
      undefined,
      accessToken,
    );
  },
  listSales(accessToken: string, tenantId: string, branchId: string) {
    return request<{ records: ControlPlaneSaleRecord[] }>(
      `/v1/tenants/${tenantId}/branches/${branchId}/sales`,
      undefined,
      accessToken,
    );
  },
  listCustomers(accessToken: string, tenantId: string, query?: string) {
    const queryParam = query ? `?query=${encodeURIComponent(query)}` : '';
    return request<{ records: ControlPlaneCustomerDirectoryRecord[] }>(
      `/v1/tenants/${tenantId}/customers${queryParam}`,
      undefined,
      accessToken,
    );
  },
  listCustomerProfiles(accessToken: string, tenantId: string, query?: string, status?: string) {
    const search = new URLSearchParams();
    if (query) {
      search.set('query', query);
    }
    if (status) {
      search.set('status', status);
    }
    const suffix = search.size ? `?${search.toString()}` : '';
    return request<{ records: ControlPlaneCustomerProfile[] }>(
      `/v1/tenants/${tenantId}/customer-profiles${suffix}`,
      undefined,
      accessToken,
    );
  },
  getCustomerProfile(accessToken: string, tenantId: string, customerProfileId: string) {
    return request<ControlPlaneCustomerProfile>(
      `/v1/tenants/${tenantId}/customer-profiles/${customerProfileId}`,
      undefined,
      accessToken,
    );
  },
  createCustomerProfile(
    accessToken: string,
    tenantId: string,
    payload: {
      full_name: string;
      phone?: string | null;
      email?: string | null;
      gstin?: string | null;
      default_note?: string | null;
      tags?: string[];
    },
  ) {
    return request<ControlPlaneCustomerProfile>(
      `/v1/tenants/${tenantId}/customer-profiles`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  updateCustomerProfile(
    accessToken: string,
    tenantId: string,
    customerProfileId: string,
    payload: {
      full_name?: string | null;
      phone?: string | null;
      email?: string | null;
      gstin?: string | null;
      default_note?: string | null;
      tags?: string[];
    },
  ) {
    return request<ControlPlaneCustomerProfile>(
      `/v1/tenants/${tenantId}/customer-profiles/${customerProfileId}`,
      {
        method: 'PATCH',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  archiveCustomerProfile(accessToken: string, tenantId: string, customerProfileId: string) {
    return request<ControlPlaneCustomerProfile>(
      `/v1/tenants/${tenantId}/customer-profiles/${customerProfileId}/archive`,
      {
        method: 'POST',
      },
      accessToken,
    );
  },
  reactivateCustomerProfile(accessToken: string, tenantId: string, customerProfileId: string) {
    return request<ControlPlaneCustomerProfile>(
      `/v1/tenants/${tenantId}/customer-profiles/${customerProfileId}/reactivate`,
      {
        method: 'POST',
      },
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
  listRuntimeSyncEnvelopes(accessToken: string, tenantId: string, branchId: string) {
    return request<{ records: ControlPlaneSyncEnvelopeRecord[] }>(
      `/v1/tenants/${tenantId}/branches/${branchId}/runtime/sync-envelopes`,
      undefined,
      accessToken,
    );
  },
  createGstExport(accessToken: string, tenantId: string, branchId: string, payload: { sale_id: string }) {
    return request<ControlPlaneGstExportJob>(
      `/v1/tenants/${tenantId}/branches/${branchId}/compliance/gst-exports`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  listGstExports(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneGstExportReport>(
      `/v1/tenants/${tenantId}/branches/${branchId}/compliance/gst-exports`,
      undefined,
      accessToken,
    );
  },
  getComplianceProviderProfile(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneComplianceProviderProfile>(
      `/v1/tenants/${tenantId}/branches/${branchId}/compliance/provider-profile`,
      undefined,
      accessToken,
    );
  },
  updateComplianceProviderProfile(
    accessToken: string,
    tenantId: string,
    branchId: string,
    payload: { provider_name: string; api_username: string; api_password?: string | null },
  ) {
    return request<ControlPlaneComplianceProviderProfile>(
      `/v1/tenants/${tenantId}/branches/${branchId}/compliance/provider-profile`,
      {
        method: 'PUT',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  retryGstExportSubmission(accessToken: string, tenantId: string, branchId: string, jobId: string) {
    return request<ControlPlaneGstExportJob>(
      `/v1/tenants/${tenantId}/branches/${branchId}/compliance/gst-exports/${jobId}/retry-submission`,
      {
        method: 'POST',
      },
      accessToken,
    );
  },
  approveSaleReturnRefund(
    accessToken: string,
    tenantId: string,
    branchId: string,
    saleReturnId: string,
    payload: { note?: string | null },
  ) {
    return request<ControlPlaneSaleReturn>(
      `/v1/tenants/${tenantId}/branches/${branchId}/sale-returns/${saleReturnId}/approve-refund`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  createStockAdjustment(
    accessToken: string,
    tenantId: string,
    branchId: string,
    payload: { product_id: string; quantity_delta: number; reason: string; note?: string | null },
  ) {
    return request<ControlPlaneStockAdjustment>(
      `/v1/tenants/${tenantId}/branches/${branchId}/stock-adjustments`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  createStockCount(
    accessToken: string,
    tenantId: string,
    branchId: string,
    payload: { product_id: string; counted_quantity: number; note?: string | null },
  ) {
    return request<ControlPlaneStockCount>(
      `/v1/tenants/${tenantId}/branches/${branchId}/stock-counts`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  createStockCountSession(
    accessToken: string,
    tenantId: string,
    branchId: string,
    payload: { product_id: string; note?: string | null },
  ) {
    return request<ControlPlaneStockCountReviewSession>(
      `/v1/tenants/${tenantId}/branches/${branchId}/stock-count-sessions`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  recordStockCountSession(
    accessToken: string,
    tenantId: string,
    branchId: string,
    stockCountSessionId: string,
    payload: { counted_quantity: number; note?: string | null },
  ) {
    return request<ControlPlaneStockCountReviewSession>(
      `/v1/tenants/${tenantId}/branches/${branchId}/stock-count-sessions/${stockCountSessionId}/record`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  approveStockCountSession(
    accessToken: string,
    tenantId: string,
    branchId: string,
    stockCountSessionId: string,
    payload: { review_note?: string | null },
  ) {
    return request<ControlPlaneStockCountApproval>(
      `/v1/tenants/${tenantId}/branches/${branchId}/stock-count-sessions/${stockCountSessionId}/approve`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  cancelStockCountSession(
    accessToken: string,
    tenantId: string,
    branchId: string,
    stockCountSessionId: string,
    payload: { review_note?: string | null },
  ) {
    return request<ControlPlaneStockCountReviewSession>(
      `/v1/tenants/${tenantId}/branches/${branchId}/stock-count-sessions/${stockCountSessionId}/cancel`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  getStockCountBoard(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneStockCountBoard>(
      `/v1/tenants/${tenantId}/branches/${branchId}/stock-count-board`,
      undefined,
      accessToken,
    );
  },
  createTransfer(
    accessToken: string,
    tenantId: string,
    branchId: string,
    payload: { destination_branch_id: string; product_id: string; quantity: number; note?: string | null },
  ) {
    return request<ControlPlaneTransfer>(
      `/v1/tenants/${tenantId}/branches/${branchId}/transfers`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  getTransferBoard(accessToken: string, tenantId: string, branchId: string) {
    return request<ControlPlaneTransferBoard>(
      `/v1/tenants/${tenantId}/branches/${branchId}/transfer-board`,
      undefined,
      accessToken,
    );
  },
  submitPurchaseOrderApproval(
    accessToken: string,
    tenantId: string,
    branchId: string,
    purchaseOrderId: string,
    payload: { note?: string | null },
  ) {
    return request<ControlPlanePurchaseOrder>(
      `/v1/tenants/${tenantId}/branches/${branchId}/purchase-orders/${purchaseOrderId}/submit-approval`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  approvePurchaseOrder(
    accessToken: string,
    tenantId: string,
    branchId: string,
    purchaseOrderId: string,
    payload: { note?: string | null },
  ) {
    return request<ControlPlanePurchaseOrder>(
      `/v1/tenants/${tenantId}/branches/${branchId}/purchase-orders/${purchaseOrderId}/approve`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  listBranchDevices(accessToken: string, tenantId: string, branchId: string) {
    return request<{ records: ControlPlaneDeviceRecord[] }>(
      `/v1/tenants/${tenantId}/branches/${branchId}/devices`,
      undefined,
      accessToken,
    );
  },
  registerBranchDevice(
    accessToken: string,
    tenantId: string,
    branchId: string,
    payload: { device_name: string; device_code: string; session_surface: string; assigned_staff_profile_id?: string | null; is_branch_hub?: boolean },
  ) {
    return request<ControlPlaneDeviceRegistration>(
      `/v1/tenants/${tenantId}/branches/${branchId}/devices`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  listBranchDeviceClaims(accessToken: string, tenantId: string, branchId: string) {
    return request<{ records: ControlPlaneDeviceClaimRecord[] }>(
      `/v1/tenants/${tenantId}/branches/${branchId}/device-claims`,
      undefined,
      accessToken,
    );
  },
  approveBranchDeviceClaim(
    accessToken: string,
    tenantId: string,
    branchId: string,
    claimId: string,
    payload: { device_name: string; device_code: string; session_surface: string; assigned_staff_profile_id?: string | null; is_branch_hub?: boolean },
  ) {
    return request<ControlPlaneDeviceClaimApproval>(
      `/v1/tenants/${tenantId}/branches/${branchId}/device-claims/${claimId}/approve`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  issueStoreDesktopActivation(accessToken: string, tenantId: string, branchId: string, deviceId: string) {
    return request<ControlPlaneStoreDesktopActivation>(
      `/v1/tenants/${tenantId}/branches/${branchId}/devices/${deviceId}/desktop-activation`,
      {
        method: 'POST',
      },
      accessToken,
    );
  },
};
