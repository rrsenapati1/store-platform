export const actorRoles = [
  'platform_super_admin',
  'tenant_owner',
  'finance_admin',
  'catalog_admin',
  'inventory_admin',
  'store_manager',
  'cashier',
  'stock_clerk',
  'sales_associate',
  'auditor',
] as const;

export type ActorRole = (typeof actorRoles)[number];

export const capabilities = [
  'catalog.manage',
  'pricing.manage',
  'barcode.manage',
  'inventory.adjust',
  'inventory.transfer',
  'purchase.manage',
  'sales.bill',
  'sales.return',
  'refund.approve',
  'reports.view',
  'compliance.export',
  'staff.manage',
  'settings.manage',
] as const;

export type Capability = (typeof capabilities)[number];

export interface BarcodeLabelModel {
  skuCode: string;
  productName: string;
  barcode: string;
  priceLabel: string;
}

export interface ThermalReceiptLineItem {
  name: string;
  qty: number;
  unitPrice: number;
  lineTotal: number;
}

export interface ThermalReceiptInput {
  invoiceNumber: string;
  customerName: string;
  gstin?: string | null;
  irnStatus: 'IRN_PENDING' | 'IRN_ATTACHED' | 'NOT_REQUIRED';
  items: ThermalReceiptLineItem[];
  totals: {
    subtotal: number;
    cgst: number;
    sgst: number;
    igst: number;
    grandTotal: number;
  };
}

export interface SyncRecord {
  id: string;
  version: number;
}

export interface MutationConflictInput {
  clientVersion: number;
  serverVersion: number;
}

export interface MutationConflictResult {
  accepted: boolean;
  conflict: boolean;
  nextVersion: number;
}

export interface PullResponse {
  cursor: number;
  records: SyncRecord[];
}

export interface WorkspaceMetric {
  label: string;
  value: string;
  tone?: 'default' | 'success' | 'warning';
}

export interface ControlPlaneTenantMembership {
  tenant_id: string;
  role_name: string;
  status: string;
}

export interface ControlPlaneBranchMembership {
  tenant_id: string;
  branch_id: string;
  role_name: string;
  status: string;
}

export interface ControlPlaneActor {
  user_id: string;
  email: string;
  full_name: string;
  is_platform_admin: boolean;
  tenant_memberships: ControlPlaneTenantMembership[];
  branch_memberships: ControlPlaneBranchMembership[];
}

export interface ControlPlaneSession {
  access_token: string;
  token_type: string;
  expires_at: string;
}

export interface ControlPlanePlatformTenantRecord {
  tenant_id: string;
  name: string;
  slug: string;
  status: string;
  onboarding_status: string;
}

export interface ControlPlaneTenant {
  id: string;
  name: string;
  slug: string;
  status: string;
  onboarding_status: string;
}

export interface ControlPlaneBranch {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
  gstin?: string | null;
  timezone?: string;
  status: string;
}

export interface ControlPlaneBranchRecord {
  branch_id: string;
  tenant_id: string;
  name: string;
  code: string;
  status: string;
}

export interface ControlPlaneInvite {
  id: string;
  tenant_id: string;
  email: string;
  full_name: string;
  status: string;
}

export interface ControlPlaneMembership {
  id: string;
  tenant_id: string;
  branch_id?: string | null;
  email: string;
  full_name: string;
  role_name: string;
  status: string;
}

export interface ControlPlaneStaffProfile {
  id: string;
  tenant_id: string;
  user_id?: string | null;
  email: string;
  full_name: string;
  phone_number?: string | null;
  primary_branch_id?: string | null;
  status: string;
}

export interface ControlPlaneStaffProfileRecord extends ControlPlaneStaffProfile {
  role_names: string[];
  branch_ids: string[];
}

export interface ControlPlaneDeviceRegistration {
  id: string;
  tenant_id: string;
  branch_id: string;
  device_name: string;
  device_code: string;
  session_surface: string;
  runtime_profile: string;
  is_branch_hub?: boolean;
  status: string;
  assigned_staff_profile_id?: string | null;
  installation_id?: string | null;
  sync_access_secret?: string | null;
  last_seen_at?: string | null;
}

export interface ControlPlaneDeviceRecord extends ControlPlaneDeviceRegistration {
  assigned_staff_full_name?: string | null;
}

export interface ControlPlaneDeviceClaimRecord {
  id: string;
  tenant_id: string;
  branch_id: string;
  installation_id: string;
  claim_code: string;
  runtime_kind: string;
  hostname?: string | null;
  operating_system?: string | null;
  architecture?: string | null;
  app_version?: string | null;
  status: string;
  approved_device_id?: string | null;
  approved_device_code?: string | null;
  created_at: string;
  last_seen_at?: string | null;
  approved_at?: string | null;
}

export interface ControlPlaneRuntimeDeviceClaimResolution {
  claim_id: string;
  claim_code: string;
  status: string;
  bound_device_id?: string | null;
  bound_device_name?: string | null;
  bound_device_code?: string | null;
}

export interface ControlPlaneRuntimeHubBootstrap {
  device_id: string;
  device_code: string;
  installation_id: string;
  sync_access_secret: string;
  issued_at: string;
}

export interface ControlPlaneDeviceClaimApproval {
  claim: ControlPlaneDeviceClaimRecord;
  device: ControlPlaneDeviceRegistration;
}

export interface ControlPlaneStoreDesktopActivation {
  device_id: string;
  staff_profile_id: string;
  activation_code: string;
  status: string;
  expires_at: string;
}

export interface ControlPlaneSpokeRuntimeActivation {
  activation_code: string;
  pairing_mode: 'approval_code' | 'qr';
  runtime_profile: string;
  hub_device_id: string;
  expires_at: string;
}

export interface ControlPlaneStoreDesktopActivationSession {
  access_token: string;
  token_type: string;
  expires_at: string;
  device_id: string;
  staff_profile_id: string;
  local_auth_token: string;
  offline_valid_until: string;
  activation_version: number;
}

export interface ControlPlaneRuntimeHeartbeat {
  device_id: string;
  status: string;
  last_seen_at?: string | null;
  queued_job_count: number;
}

export interface ControlPlaneSyncStatus {
  hub_device_id?: string | null;
  source_device_id?: string | null;
  branch_cursor: number;
  last_pull_cursor: number;
  last_heartbeat_at?: string | null;
  last_successful_push_at?: string | null;
  last_successful_pull_at?: string | null;
  last_successful_push_mutations?: number | null;
  last_idempotency_key?: string | null;
  open_conflict_count: number;
  failed_push_count: number;
  connected_spoke_count: number;
  local_outbox_depth: number;
  pending_mutation_count: number;
  oldest_unsynced_mutation_age_seconds?: number | null;
  runtime_state: string;
  last_local_spoke_sync_at?: string | null;
}

export interface ControlPlaneSyncSpokeRecord {
  spoke_device_id: string;
  hub_device_id: string;
  runtime_kind: string;
  runtime_profile: string;
  hostname?: string | null;
  operating_system?: string | null;
  app_version?: string | null;
  connection_state: string;
  last_seen_at: string;
  last_local_sync_at?: string | null;
}

export interface ControlPlaneSyncConflictRecord {
  id: string;
  device_id: string;
  source_idempotency_key: string;
  table_name: string;
  record_id: string;
  reason: string;
  message?: string | null;
  client_version?: number | null;
  server_version?: number | null;
  retry_strategy?: string | null;
  status: string;
  created_at: string;
}

export interface ControlPlaneSyncEnvelopeRecord {
  id: string;
  device_id: string;
  idempotency_key: string;
  transport: string;
  direction: string;
  entity_type: string;
  entity_id?: string | null;
  status: string;
  attempt_count: number;
  last_error?: string | null;
  created_at: string;
}

export interface ControlPlanePrintJobPayload {
  document_number?: string | null;
  customer_name?: string | null;
  receipt_lines?: string[];
  product_id?: string;
  labels?: Array<{
    sku_code: string;
    product_name: string;
    barcode: string;
    price_label: string;
  }>;
}

export interface ControlPlanePrintJob {
  id: string;
  tenant_id: string;
  branch_id: string;
  device_id: string;
  reference_type: string;
  reference_id: string;
  job_type: string;
  copies: number;
  status: string;
  failure_reason?: string | null;
  payload: ControlPlanePrintJobPayload;
}

export interface ControlPlaneCatalogProduct {
  id: string;
  tenant_id: string;
  name: string;
  sku_code: string;
  barcode: string;
  hsn_sac_code: string;
  gst_rate: number;
  selling_price: number;
  status: string;
}

export interface ControlPlaneCatalogProductRecord {
  product_id: string;
  tenant_id: string;
  name: string;
  sku_code: string;
  barcode: string;
  hsn_sac_code: string;
  gst_rate: number;
  selling_price: number;
  status: string;
}

export interface ControlPlaneBarcodeAllocation {
  product_id: string;
  barcode: string;
  source: string;
}

export interface ControlPlaneBarcodeScanLookup {
  product_id: string;
  product_name: string;
  sku_code: string;
  barcode: string;
  selling_price: number;
  stock_on_hand: number;
  availability_status: string;
}

export interface ControlPlaneBarcodeLabelPreview {
  product_id: string;
  sku_code: string;
  product_name: string;
  barcode: string;
  price_label: string;
}

export interface ControlPlaneBranchCatalogItem {
  id: string;
  tenant_id: string;
  branch_id: string;
  product_id: string;
  product_name: string;
  sku_code: string;
  barcode: string;
  hsn_sac_code: string;
  gst_rate: number;
  base_selling_price: number;
  selling_price_override?: number | null;
  effective_selling_price: number;
  availability_status: string;
}

export interface ControlPlaneSupplier {
  id: string;
  tenant_id: string;
  name: string;
  gstin?: string | null;
  payment_terms_days: number;
  status: string;
}

export interface ControlPlaneSupplierRecord {
  supplier_id: string;
  tenant_id: string;
  name: string;
  gstin?: string | null;
  payment_terms_days: number;
  status: string;
}

export interface ControlPlanePurchaseOrderLine {
  product_id: string;
  product_name: string;
  sku_code: string;
  quantity: number;
  unit_cost: number;
  line_total: number;
}

export interface ControlPlanePurchaseOrder {
  id: string;
  tenant_id: string;
  branch_id: string;
  supplier_id: string;
  purchase_order_number: string;
  approval_status: string;
  subtotal: number;
  tax_total: number;
  grand_total: number;
  lines: ControlPlanePurchaseOrderLine[];
}

export interface ControlPlanePurchaseOrderRecord {
  purchase_order_id: string;
  purchase_order_number: string;
  supplier_id: string;
  supplier_name: string;
  approval_status: string;
  line_count: number;
  ordered_quantity: number;
  grand_total: number;
  approval_requested_note?: string | null;
  approval_decision_note?: string | null;
}

export interface ControlPlanePurchaseApprovalReportRecord {
  purchase_order_id: string;
  purchase_order_number: string;
  supplier_name: string;
  approval_status: string;
  line_count: number;
  ordered_quantity: number;
  grand_total: number;
  approval_requested_note?: string | null;
  approval_decision_note?: string | null;
}

export interface ControlPlanePurchaseApprovalReport {
  branch_id: string;
  not_requested_count: number;
  pending_approval_count: number;
  approved_count: number;
  rejected_count: number;
  records: ControlPlanePurchaseApprovalReportRecord[];
}

export interface ControlPlanePurchaseInvoiceLine {
  product_id: string;
  product_name: string;
  sku_code: string;
  quantity: number;
  unit_cost: number;
  gst_rate: number;
  line_subtotal: number;
  tax_total: number;
  line_total: number;
}

export interface ControlPlanePurchaseInvoice {
  id: string;
  tenant_id: string;
  branch_id: string;
  supplier_id: string;
  goods_receipt_id: string;
  invoice_number: string;
  invoice_date: string;
  due_date: string;
  payment_terms_days: number;
  subtotal: number;
  cgst_total: number;
  sgst_total: number;
  igst_total: number;
  grand_total: number;
  lines: ControlPlanePurchaseInvoiceLine[];
}

export interface ControlPlanePurchaseInvoiceRecord {
  purchase_invoice_id: string;
  purchase_invoice_number: string;
  supplier_id: string;
  supplier_name: string;
  goods_receipt_id: string;
  goods_receipt_number: string;
  invoice_date: string;
  due_date: string;
  grand_total: number;
}

export interface ControlPlaneSupplierReturnLine {
  product_id: string;
  product_name: string;
  sku_code: string;
  quantity: number;
  unit_cost: number;
  gst_rate: number;
  line_subtotal: number;
  tax_total: number;
  line_total: number;
}

export interface ControlPlaneSupplierReturn {
  id: string;
  tenant_id: string;
  branch_id: string;
  supplier_id: string;
  purchase_invoice_id: string;
  supplier_credit_note_number: string;
  issued_on: string;
  subtotal: number;
  cgst_total: number;
  sgst_total: number;
  igst_total: number;
  grand_total: number;
  lines: ControlPlaneSupplierReturnLine[];
}

export interface ControlPlaneSupplierPayment {
  id: string;
  tenant_id: string;
  branch_id: string;
  supplier_id: string;
  purchase_invoice_id: string;
  payment_number: string;
  paid_on: string;
  payment_method: string;
  amount: number;
  reference?: string | null;
}

export interface ControlPlaneSupplierPayablesReportRecord {
  purchase_invoice_id: string;
  purchase_invoice_number: string;
  supplier_name: string;
  grand_total: number;
  credit_note_total: number;
  paid_total: number;
  outstanding_total: number;
  settlement_status: string;
}

export interface ControlPlaneSupplierPayablesReport {
  branch_id: string;
  invoiced_total: number;
  credit_note_total: number;
  paid_total: number;
  outstanding_total: number;
  records: ControlPlaneSupplierPayablesReportRecord[];
}

export interface ControlPlaneSupplierAgingRecord {
  purchase_invoice_id: string;
  purchase_invoice_number: string;
  supplier_name: string;
  invoice_date: string;
  invoice_age_days: number;
  grand_total: number;
  credit_note_total: number;
  paid_total: number;
  outstanding_total: number;
  aging_bucket: string;
}

export interface ControlPlaneSupplierAgingReport {
  branch_id: string;
  as_of_date: string;
  open_invoice_count: number;
  current_total: number;
  days_1_30_total: number;
  days_31_60_total: number;
  days_61_plus_total: number;
  outstanding_total: number;
  records: ControlPlaneSupplierAgingRecord[];
}

export interface ControlPlaneSupplierStatementRecord {
  supplier_id: string;
  supplier_name: string;
  invoice_count: number;
  open_invoice_count: number;
  invoiced_total: number;
  credit_note_total: number;
  paid_total: number;
  outstanding_total: number;
}

export interface ControlPlaneSupplierStatementReport {
  branch_id: string;
  as_of_date: string;
  supplier_count: number;
  open_supplier_count: number;
  outstanding_total: number;
  records: ControlPlaneSupplierStatementRecord[];
}

export interface ControlPlaneSupplierDueScheduleRecord {
  purchase_invoice_id: string;
  purchase_invoice_number: string;
  supplier_id: string;
  supplier_name: string;
  due_date: string;
  outstanding_total: number;
  due_status: string;
}

export interface ControlPlaneSupplierDueScheduleReport {
  branch_id: string;
  as_of_date: string;
  overdue_invoice_count: number;
  overdue_total: number;
  due_today_total: number;
  due_in_7_days_total: number;
  due_in_8_30_days_total: number;
  due_later_total: number;
  records: ControlPlaneSupplierDueScheduleRecord[];
}

export interface ControlPlaneVendorDisputeRecord {
  dispute_id: string;
  supplier_id: string;
  supplier_name: string;
  reference_type: string;
  reference_number?: string | null;
  dispute_type: string;
  status: string;
  opened_on?: string | null;
  resolved_on?: string | null;
  age_days: number;
  overdue: boolean;
}

export interface ControlPlaneVendorDisputeBoard {
  branch_id: string;
  as_of_date: string;
  open_count: number;
  resolved_count: number;
  overdue_open_count: number;
  records: ControlPlaneVendorDisputeRecord[];
}

export interface ControlPlaneSupplierExceptionRecord {
  supplier_id: string;
  supplier_name: string;
  dispute_count: number;
  open_count: number;
  resolved_count: number;
  overdue_open_count: number;
  latest_dispute_type?: string | null;
  latest_reference_type?: string | null;
  latest_reference_number?: string | null;
  latest_opened_on?: string | null;
  status: string;
}

export interface ControlPlaneSupplierExceptionReport {
  branch_id: string;
  as_of_date: string;
  supplier_count: number;
  suppliers_with_open_disputes: number;
  suppliers_with_overdue_disputes: number;
  records: ControlPlaneSupplierExceptionRecord[];
}

export interface ControlPlaneSupplierSettlementRecord {
  supplier_id: string;
  supplier_name: string;
  outstanding_total: number;
  overdue_total: number;
  due_in_7_days_total: number;
  risk_status: string;
}

export interface ControlPlaneSupplierSettlementReport {
  branch_id: string;
  as_of_date: string;
  supplier_count: number;
  overdue_total: number;
  due_in_7_days_total: number;
  outstanding_total: number;
  records: ControlPlaneSupplierSettlementRecord[];
}

export interface ControlPlaneSupplierSettlementBlockerRecord {
  supplier_id: string;
  supplier_name: string;
  hold_status: string;
  open_dispute_count: number;
  overdue_open_dispute_count: number;
  outstanding_total: number;
  release_now_total: number;
  release_this_week_total: number;
}

export interface ControlPlaneSupplierSettlementBlockerReport {
  branch_id: string;
  as_of_date: string;
  supplier_count: number;
  hard_hold_count: number;
  soft_hold_count: number;
  blocked_release_now_total: number;
  blocked_release_this_week_total: number;
  blocked_outstanding_total: number;
  records: ControlPlaneSupplierSettlementBlockerRecord[];
}

export interface ControlPlaneSupplierEscalationRecord {
  dispute_id: string;
  supplier_id: string;
  supplier_name: string;
  escalation_status: string;
  escalation_target: string;
  blocked_release_now_total: number;
  blocked_release_this_week_total: number;
  age_days: number;
}

export interface ControlPlaneSupplierEscalationReport {
  branch_id: string;
  as_of_date: string;
  open_case_count: number;
  finance_escalation_count: number;
  owner_escalation_count: number;
  stale_case_count: number;
  branch_follow_up_count: number;
  blocked_release_now_total: number;
  blocked_release_this_week_total: number;
  blocked_outstanding_total: number;
  records: ControlPlaneSupplierEscalationRecord[];
}

export interface ControlPlaneSupplierPerformanceRecord {
  supplier_id: string;
  supplier_name: string;
  approved_purchase_order_count: number;
  received_purchase_order_count: number;
  on_time_receipt_rate: number;
  supplier_return_rate: number;
  invoice_mismatch_rate: number;
  average_receipt_delay_days: number;
  performance_status: string;
}

export interface ControlPlaneSupplierPerformanceReport {
  branch_id: string;
  supplier_count: number;
  at_risk_count: number;
  watch_count: number;
  good_count: number;
  records: ControlPlaneSupplierPerformanceRecord[];
}

export interface ControlPlaneSupplierPaymentActivityRecord {
  supplier_id: string;
  supplier_name: string;
  payment_count: number;
  paid_total: number;
  recent_30_days_paid_total: number;
  average_payment_value: number;
  outstanding_total: number;
  last_payment_date?: string | null;
  last_payment_method?: string | null;
  last_payment_amount?: number | null;
}

export interface ControlPlaneSupplierPaymentActivityReport {
  branch_id: string;
  as_of_date: string;
  supplier_count: number;
  payment_count: number;
  paid_total: number;
  recent_30_days_paid_total: number;
  records: ControlPlaneSupplierPaymentActivityRecord[];
}

export interface ControlPlaneGoodsReceiptLine {
  product_id: string;
  product_name: string;
  sku_code: string;
  quantity: number;
  unit_cost: number;
  line_total: number;
}

export interface ControlPlaneGoodsReceipt {
  id: string;
  tenant_id: string;
  branch_id: string;
  purchase_order_id: string;
  supplier_id: string;
  goods_receipt_number: string;
  received_on: string;
  lines: ControlPlaneGoodsReceiptLine[];
}

export interface ControlPlaneGoodsReceiptRecord {
  goods_receipt_id: string;
  goods_receipt_number: string;
  purchase_order_id: string;
  purchase_order_number: string;
  supplier_id: string;
  supplier_name: string;
  received_on: string;
  line_count: number;
  received_quantity: number;
}

export interface ControlPlaneBatchLot {
  id: string;
  product_id: string;
  batch_number: string;
  quantity: number;
  expiry_date: string;
}

export interface ControlPlaneGoodsReceiptBatchLotIntake {
  goods_receipt_id: string;
  records: ControlPlaneBatchLot[];
}

export interface ControlPlaneReceivingBoardRecord {
  purchase_order_id: string;
  purchase_order_number: string;
  supplier_name: string;
  approval_status: string;
  receiving_status: string;
  can_receive: boolean;
  blocked_reason?: string | null;
  goods_receipt_id?: string | null;
}

export interface ControlPlaneReceivingBoard {
  branch_id: string;
  blocked_count: number;
  ready_count: number;
  received_count: number;
  records: ControlPlaneReceivingBoardRecord[];
}

export interface ControlPlaneInventoryLedgerRecord {
  inventory_ledger_entry_id: string;
  product_id: string;
  product_name: string;
  sku_code: string;
  entry_type: string;
  quantity: number;
  reference_type: string;
  reference_id: string;
}

export interface ControlPlaneInventorySnapshotRecord {
  product_id: string;
  product_name: string;
  sku_code: string;
  stock_on_hand: number;
  last_entry_type: string;
}

export interface ControlPlaneBatchExpiryReportRecord {
  batch_lot_id: string;
  product_id: string;
  product_name: string;
  batch_number: string;
  expiry_date: string;
  days_to_expiry: number;
  received_quantity: number;
  written_off_quantity: number;
  remaining_quantity: number;
  status: string;
}

export interface ControlPlaneBatchExpiryReport {
  branch_id: string;
  tracked_lot_count: number;
  expiring_soon_count: number;
  expired_count: number;
  untracked_stock_quantity: number;
  records: ControlPlaneBatchExpiryReportRecord[];
}

export interface ControlPlaneBatchExpiryWriteOff {
  batch_lot_id: string;
  product_id: string;
  product_name: string;
  batch_number: string;
  expiry_date: string;
  received_quantity: number;
  written_off_quantity: number;
  remaining_quantity: number;
  status: string;
  reason: string;
}

export interface ControlPlaneStockAdjustment {
  id: string;
  tenant_id: string;
  branch_id: string;
  product_id: string;
  quantity_delta: number;
  reason: string;
  note?: string | null;
  resulting_stock_on_hand: number;
}

export interface ControlPlaneStockCount {
  id: string;
  tenant_id: string;
  branch_id: string;
  product_id: string;
  counted_quantity: number;
  expected_quantity: number;
  variance_quantity: number;
  note?: string | null;
  closing_stock: number;
}

export interface ControlPlaneTransfer {
  id: string;
  tenant_id: string;
  source_branch_id: string;
  destination_branch_id: string;
  product_id: string;
  transfer_number: string;
  quantity: number;
  status: string;
  note?: string | null;
}

export interface ControlPlaneTransferBoardRecord {
  transfer_order_id: string;
  transfer_number: string;
  direction: string;
  counterparty_branch_id: string;
  counterparty_branch_name: string;
  product_id: string;
  product_name: string;
  sku_code: string;
  quantity: number;
  status: string;
}

export interface ControlPlaneTransferBoard {
  branch_id: string;
  outbound_count: number;
  inbound_count: number;
  records: ControlPlaneTransferBoardRecord[];
}

export interface ControlPlanePayment {
  payment_method: string;
  amount: number;
}

export interface ControlPlaneSaleLine {
  product_id: string;
  product_name: string;
  sku_code: string;
  hsn_sac_code: string;
  quantity: number;
  unit_price: number;
  gst_rate: number;
  line_subtotal: number;
  tax_total: number;
  line_total: number;
}

export interface ControlPlaneInvoiceTaxLine {
  tax_type: string;
  tax_rate: number;
  taxable_amount: number;
  tax_amount: number;
}

export interface ControlPlaneSale {
  id: string;
  tenant_id: string;
  branch_id: string;
  customer_name: string;
  customer_gstin?: string | null;
  invoice_kind: string;
  irn_status: string;
  invoice_number: string;
  issued_on: string;
  subtotal: number;
  cgst_total: number;
  sgst_total: number;
  igst_total: number;
  grand_total: number;
  payment: ControlPlanePayment;
  lines: ControlPlaneSaleLine[];
  tax_lines: ControlPlaneInvoiceTaxLine[];
}

export interface ControlPlaneSaleRecord {
  sale_id: string;
  invoice_number: string;
  customer_name: string;
  invoice_kind: string;
  irn_status: string;
  payment_method: string;
  grand_total: number;
  issued_on: string;
}

export interface ControlPlaneCustomerDirectoryRecord {
  customer_id: string;
  name: string;
  phone?: string | null;
  email?: string | null;
  gstin?: string | null;
  visit_count: number;
  lifetime_value: number;
  last_sale_id?: string | null;
  last_invoice_number?: string | null;
  last_branch_id?: string | null;
}

export interface ControlPlaneCustomerHistoryCustomer {
  customer_id: string;
  name: string;
  phone?: string | null;
  email?: string | null;
  gstin?: string | null;
  visit_count: number;
  lifetime_value: number;
  last_sale_id?: string | null;
}

export interface ControlPlaneCustomerHistorySummary {
  sales_count: number;
  sales_total: number;
  return_count: number;
  credit_note_total: number;
  exchange_count: number;
}

export interface ControlPlaneCustomerSaleHistory {
  sale_id: string;
  branch_id: string;
  invoice_id: string;
  invoice_number: string;
  grand_total: number;
  payment_method: string;
}

export interface ControlPlaneCustomerReturnHistory {
  sale_return_id: string;
  sale_id: string;
  branch_id: string;
  credit_note_id: string;
  credit_note_number: string;
  grand_total: number;
  refund_amount: number;
  status: string;
}

export interface ControlPlaneCustomerExchangeHistory {
  exchange_order_id: string;
  sale_id: string;
  branch_id: string;
  return_total: number;
  replacement_total: number;
  balance_direction: string;
  balance_amount: number;
}

export interface ControlPlaneCustomerHistoryResponse {
  customer: ControlPlaneCustomerHistoryCustomer;
  sales_summary: ControlPlaneCustomerHistorySummary;
  sales: ControlPlaneCustomerSaleHistory[];
  returns: ControlPlaneCustomerReturnHistory[];
  exchanges: ControlPlaneCustomerExchangeHistory[];
}

export interface ControlPlaneBranchCustomerTopRecord {
  customer_id: string;
  customer_name: string;
  sales_count: number;
  sales_total: number;
  last_invoice_number?: string | null;
}

export interface ControlPlaneBranchCustomerReturnRecord {
  customer_id: string;
  customer_name: string;
  return_count: number;
  credit_note_total: number;
  exchange_count: number;
}

export interface ControlPlaneBranchCustomerReport {
  branch_id: string;
  customer_count: number;
  repeat_customer_count: number;
  anonymous_sales_count: number;
  anonymous_sales_total: number;
  top_customers: ControlPlaneBranchCustomerTopRecord[];
  return_activity: ControlPlaneBranchCustomerReturnRecord[];
}

export interface ControlPlaneGstExportJob {
  id: string;
  sale_id: string;
  invoice_id: string;
  invoice_number: string;
  customer_name: string;
  seller_gstin: string;
  buyer_gstin?: string | null;
  hsn_sac_summary: string;
  grand_total: number;
  status: string;
  irn?: string | null;
  ack_no?: string | null;
  signed_qr_payload?: string | null;
  created_at: string;
}

export interface ControlPlaneGstExportReport {
  branch_id: string;
  pending_count: number;
  attached_count: number;
  records: ControlPlaneGstExportJob[];
}

export interface ControlPlaneCreditNoteTaxLine {
  tax_type: string;
  tax_rate: number;
  taxable_amount: number;
  tax_amount: number;
}

export interface ControlPlaneCreditNote {
  id: string;
  credit_note_number: string;
  issued_on: string;
  subtotal: number;
  cgst_total: number;
  sgst_total: number;
  igst_total: number;
  grand_total: number;
  tax_lines: ControlPlaneCreditNoteTaxLine[];
}

export interface ControlPlaneSaleReturnLine {
  product_id: string;
  product_name: string;
  sku_code: string;
  hsn_sac_code: string;
  quantity: number;
  unit_price: number;
  gst_rate: number;
  line_subtotal: number;
  tax_total: number;
  line_total: number;
}

export interface ControlPlaneSaleReturn {
  id: string;
  tenant_id: string;
  branch_id: string;
  sale_id: string;
  status: string;
  refund_amount: number;
  refund_method: string;
  lines: ControlPlaneSaleReturnLine[];
  credit_note: ControlPlaneCreditNote;
}

export interface ControlPlaneSaleReturnRecord {
  sale_return_id: string;
  sale_id: string;
  invoice_number: string;
  customer_name: string;
  status: string;
  refund_amount: number;
  refund_method: string;
  credit_note_number: string;
  credit_note_total: number;
  issued_on: string;
}

export interface ControlPlaneExchangePaymentAllocation {
  payment_method: string;
  amount: number;
}

export interface ControlPlaneExchange {
  id: string;
  tenant_id: string;
  branch_id: string;
  original_sale_id: string;
  replacement_sale_id: string;
  sale_return_id: string;
  status: string;
  balance_direction: string;
  balance_amount: number;
  settlement_method: string;
  payment_allocations: ControlPlaneExchangePaymentAllocation[];
  sale_return: ControlPlaneSaleReturn;
  replacement_sale: ControlPlaneSale;
}

export interface ControlPlaneAuditRecord {
  id: string;
  action: string;
  entity_type: string;
  entity_id: string;
  tenant_id?: string | null;
  branch_id?: string | null;
  created_at: string;
  payload: Record<string, unknown>;
}
