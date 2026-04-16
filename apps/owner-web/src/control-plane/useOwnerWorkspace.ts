import { startTransition, useEffect, useState } from 'react';
import type {
  ControlPlaneActor,
  ControlPlaneAuditRecord,
  ControlPlaneBatchExpiryBoard,
  ControlPlaneBatchExpiryReport,
  ControlPlaneBatchExpiryReviewSession,
  ControlPlaneBatchExpiryWriteOff,
  ControlPlaneGoodsReceiptBatchLotIntake,
  ControlPlaneBarcodeAllocation, ControlPlaneBarcodeLabelPreview,
  ControlPlaneBranchCatalogItem,
  ControlPlaneBranchRecord,
  ControlPlaneCatalogProduct,
  ControlPlaneCatalogProductRecord,
  ControlPlaneDeviceRecord,
  ControlPlaneDeviceRegistration,
  ControlPlaneGoodsReceipt,
  ControlPlaneGoodsReceiptRecord,
  ControlPlaneInventoryLedgerRecord,
  ControlPlaneInventorySnapshotRecord,
  ControlPlaneMembership,
  ControlPlanePurchaseApprovalReport,
  ControlPlanePurchaseApprovalReportRecord,
  ControlPlanePurchaseInvoice,
  ControlPlanePurchaseInvoiceRecord,
  ControlPlanePurchaseOrder,
  ControlPlanePurchaseOrderRecord,
  ControlPlaneReplenishmentBoard,
  ControlPlaneRestockBoard,
  ControlPlaneRestockTask,
  ControlPlaneReceivingBoard,
  ControlPlaneSupplierPayablesReport, ControlPlaneSupplierPayment, ControlPlaneSupplierReturn,
  ControlPlaneStaffProfile,
  ControlPlaneStaffProfileRecord,
  ControlPlaneStockAdjustment,
  ControlPlaneStockCountBoard,
  ControlPlaneStockCount,
  ControlPlaneStockCountReviewSession,
  ControlPlaneSupplier,
  ControlPlaneSupplierRecord,
  ControlPlaneTenant,
  ControlPlaneTransfer,
  ControlPlaneTransferBoard,
} from '@store/types';
import { ownerControlPlaneClient } from './client';
import { runApproveBatchExpirySession, runCancelBatchExpirySession, runCreateBatchExpirySession, runLoadBatchExpiryReport, runRecordBatchExpirySession, runRecordBatchLotsOnLatestGoodsReceipt } from './batchExpiryActions';
import { runAllocateCatalogBarcode, runAssignFirstProductToBranch, runCreateCatalogProduct, runPreviewBarcodeLabel } from './catalogBarcodeActions';
import { runApproveStockCountSession, runCancelStockCountSession, runCreateBranchTransfer, runCreateGoodsReceipt, runCreateStockAdjustment, runCreateStockCountSession, runRecordStockCountSession } from './inventoryActions';
import { runAssignBranchRole, runAssignTenantRole } from './membershipActions';
import { runCreateFirstBranch, runRegisterBranchDevice } from './onboardingActions';
import { runCreatePurchaseOrder, runCreateSupplier } from './procurementActions';
import { runCreatePurchaseInvoice, runCreateSupplierPayment, runCreateSupplierReturn } from './procurementFinanceActions';
import { runLoadReplenishmentBoard, runUpdateFirstBranchReplenishmentPolicy } from './replenishmentActions';
import { runCancelRestockTask, runCompleteRestockTask, runCreateRestockTask, runLoadRestockBoard, runPickRestockTask } from './restockActions';

type ReceivingLineDraft = {
  product_id: string;
  received_quantity: string;
  discrepancy_note: string;
};

export function useOwnerWorkspace() {
  const [korsenexToken, setKorsenexToken] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [actor, setActor] = useState<ControlPlaneActor | null>(null);
  const [tenant, setTenant] = useState<ControlPlaneTenant | null>(null);
  const [branches, setBranches] = useState<ControlPlaneBranchRecord[]>([]);
  const [catalogProducts, setCatalogProducts] = useState<ControlPlaneCatalogProductRecord[]>([]);
  const [branchCatalogItems, setBranchCatalogItems] = useState<ControlPlaneBranchCatalogItem[]>([]);
  const [staffProfiles, setStaffProfiles] = useState<ControlPlaneStaffProfileRecord[]>([]);
  const [devices, setDevices] = useState<ControlPlaneDeviceRecord[]>([]);
  const [suppliers, setSuppliers] = useState<ControlPlaneSupplierRecord[]>([]);
  const [purchaseOrders, setPurchaseOrders] = useState<ControlPlanePurchaseOrderRecord[]>([]);
  const [purchaseApprovalReport, setPurchaseApprovalReport] = useState<ControlPlanePurchaseApprovalReport | null>(null);
  const [purchaseInvoices, setPurchaseInvoices] = useState<ControlPlanePurchaseInvoiceRecord[]>([]);
  const [supplierPayablesReport, setSupplierPayablesReport] = useState<ControlPlaneSupplierPayablesReport | null>(null);
  const [goodsReceipts, setGoodsReceipts] = useState<ControlPlaneGoodsReceiptRecord[]>([]);
  const [batchExpiryReport, setBatchExpiryReport] = useState<ControlPlaneBatchExpiryReport | null>(null);
  const [batchExpiryBoard, setBatchExpiryBoard] = useState<ControlPlaneBatchExpiryBoard | null>(null);
  const [receivingBoard, setReceivingBoard] = useState<ControlPlaneReceivingBoard | null>(null);
  const [inventoryLedger, setInventoryLedger] = useState<ControlPlaneInventoryLedgerRecord[]>([]);
  const [inventorySnapshot, setInventorySnapshot] = useState<ControlPlaneInventorySnapshotRecord[]>([]);
  const [stockCountBoard, setStockCountBoard] = useState<ControlPlaneStockCountBoard | null>(null);
  const [transferBoard, setTransferBoard] = useState<ControlPlaneTransferBoard | null>(null);
  const [replenishmentBoard, setReplenishmentBoard] = useState<ControlPlaneReplenishmentBoard | null>(null);
  const [restockBoard, setRestockBoard] = useState<ControlPlaneRestockBoard | null>(null);
  const [auditEvents, setAuditEvents] = useState<ControlPlaneAuditRecord[]>([]);
  const [branchName, setBranchName] = useState('');
  const [branchCode, setBranchCode] = useState('');
  const [branchGstin, setBranchGstin] = useState('');
  const [productName, setProductName] = useState('');
  const [productSkuCode, setProductSkuCode] = useState('');
  const [productBarcode, setProductBarcode] = useState('');
  const [barcodeManualValue, setBarcodeManualValue] = useState('');
  const [productHsnSacCode, setProductHsnSacCode] = useState('');
  const [productGstRate, setProductGstRate] = useState('5');
  const [productSellingPrice, setProductSellingPrice] = useState('');
  const [branchCatalogPriceOverride, setBranchCatalogPriceOverride] = useState('');
  const [supplierName, setSupplierName] = useState('');
  const [supplierGstin, setSupplierGstin] = useState('');
  const [supplierPaymentTermsDays, setSupplierPaymentTermsDays] = useState('14');
  const [purchaseQuantity, setPurchaseQuantity] = useState('');
  const [purchaseUnitCost, setPurchaseUnitCost] = useState('');
  const [approvalNote, setApprovalNote] = useState('');
  const [decisionNote, setDecisionNote] = useState('');
  const [supplierReturnQuantity, setSupplierReturnQuantity] = useState('');
  const [supplierPaymentAmount, setSupplierPaymentAmount] = useState('');
  const [supplierPaymentMethod, setSupplierPaymentMethod] = useState('bank_transfer');
  const [supplierPaymentReference, setSupplierPaymentReference] = useState('');
  const [goodsReceiptNote, setGoodsReceiptNote] = useState('');
  const [receivingLineDrafts, setReceivingLineDrafts] = useState<ReceivingLineDraft[]>([]);
  const [adjustmentDelta, setAdjustmentDelta] = useState('');
  const [adjustmentReason, setAdjustmentReason] = useState('');
  const [countedQuantity, setCountedQuantity] = useState('');
  const [countNote, setCountNote] = useState('');
  const [blindCountedQuantity, setBlindCountedQuantity] = useState('');
  const [stockCountReviewNote, setStockCountReviewNote] = useState('Approved after blind count review');
  const [transferQuantity, setTransferQuantity] = useState('');
  const [transferDestinationBranchId, setTransferDestinationBranchId] = useState('');
  const [lotABatchNumber, setLotABatchNumber] = useState('');
  const [lotAQuantity, setLotAQuantity] = useState('');
  const [lotAExpiryDate, setLotAExpiryDate] = useState('');
  const [lotBBatchNumber, setLotBBatchNumber] = useState('');
  const [lotBQuantity, setLotBQuantity] = useState('');
  const [lotBExpiryDate, setLotBExpiryDate] = useState('');
  const [expirySessionNote, setExpirySessionNote] = useState('Shelf check before disposal');
  const [expiryWriteOffQuantity, setExpiryWriteOffQuantity] = useState('');
  const [expiryWriteOffReason, setExpiryWriteOffReason] = useState('');
  const [expiryReviewNote, setExpiryReviewNote] = useState('Approved after shelf review');
  const [replenishmentReorderPoint, setReplenishmentReorderPoint] = useState('');
  const [replenishmentTargetStock, setReplenishmentTargetStock] = useState('');
  const [restockRequestedQuantity, setRestockRequestedQuantity] = useState('');
  const [restockPickedQuantity, setRestockPickedQuantity] = useState('');
  const [restockSourcePosture, setRestockSourcePosture] = useState('BACKROOM_AVAILABLE');
  const [restockNote, setRestockNote] = useState('');
  const [restockCompletionNote, setRestockCompletionNote] = useState('');
  const [staffProfileEmail, setStaffProfileEmail] = useState('');
  const [staffProfileFullName, setStaffProfileFullName] = useState('');
  const [staffProfilePhone, setStaffProfilePhone] = useState('');
  const [tenantStaffEmail, setTenantStaffEmail] = useState('');
  const [tenantStaffFullName, setTenantStaffFullName] = useState('');
  const [branchStaffEmail, setBranchStaffEmail] = useState('');
  const [branchStaffFullName, setBranchStaffFullName] = useState('');
  const [deviceName, setDeviceName] = useState('');
  const [deviceCode, setDeviceCode] = useState('');
  const [latestCatalogProduct, setLatestCatalogProduct] = useState<ControlPlaneCatalogProduct | null>(null);
  const [latestBarcodeAllocation, setLatestBarcodeAllocation] = useState<ControlPlaneBarcodeAllocation | null>(null);
  const [latestBarcodeLabelPreview, setLatestBarcodeLabelPreview] = useState<ControlPlaneBarcodeLabelPreview | null>(null);
  const [latestBranchCatalogItem, setLatestBranchCatalogItem] = useState<ControlPlaneBranchCatalogItem | null>(null);
  const [latestSupplier, setLatestSupplier] = useState<ControlPlaneSupplier | null>(null);
  const [latestPurchaseOrder, setLatestPurchaseOrder] = useState<ControlPlanePurchaseOrder | null>(null);
  const [latestApprovalState, setLatestApprovalState] = useState<ControlPlanePurchaseApprovalReportRecord | null>(null);
  const [latestGoodsReceipt, setLatestGoodsReceipt] = useState<ControlPlaneGoodsReceipt | null>(null);
  const [latestBatchLotIntake, setLatestBatchLotIntake] = useState<ControlPlaneGoodsReceiptBatchLotIntake | null>(null);
  const [latestPurchaseInvoice, setLatestPurchaseInvoice] = useState<ControlPlanePurchaseInvoice | null>(null);
  const [latestBatchExpirySession, setLatestBatchExpirySession] = useState<ControlPlaneBatchExpiryReviewSession | null>(null);
  const [latestBatchExpiryWriteOff, setLatestBatchExpiryWriteOff] = useState<ControlPlaneBatchExpiryWriteOff | null>(null);
  const [latestSupplierReturn, setLatestSupplierReturn] = useState<ControlPlaneSupplierReturn | null>(null);
  const [latestSupplierPayment, setLatestSupplierPayment] = useState<ControlPlaneSupplierPayment | null>(null);
  const [latestStockAdjustment, setLatestStockAdjustment] = useState<ControlPlaneStockAdjustment | null>(null);
  const [latestStockCount, setLatestStockCount] = useState<ControlPlaneStockCount | null>(null);
  const [latestStockCountSession, setLatestStockCountSession] = useState<ControlPlaneStockCountReviewSession | null>(null);
  const [latestTransfer, setLatestTransfer] = useState<ControlPlaneTransfer | null>(null);
  const [latestRestockTask, setLatestRestockTask] = useState<ControlPlaneRestockTask | null>(null);
  const [latestStaffProfile, setLatestStaffProfile] = useState<ControlPlaneStaffProfile | null>(null);
  const [latestTenantMembership, setLatestTenantMembership] = useState<ControlPlaneMembership | null>(null);
  const [latestBranchMembership, setLatestBranchMembership] = useState<ControlPlaneMembership | null>(null);
  const [latestDevice, setLatestDevice] = useState<ControlPlaneDeviceRegistration | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  const tenantId = actor?.tenant_memberships[0]?.tenant_id ?? '';
  const branchId = branches[0]?.branch_id ?? '';

  useEffect(() => {
    if (!latestPurchaseOrder) {
      setGoodsReceiptNote('');
      setReceivingLineDrafts([]);
      return;
    }
    setGoodsReceiptNote('');
    setReceivingLineDrafts(
      latestPurchaseOrder.lines.map((line) => ({
        product_id: line.product_id,
        received_quantity: String(line.quantity),
        discrepancy_note: '',
      })),
    );
  }, [latestPurchaseOrder?.id]);

  function setReceivingLineQuantity(productId: string, value: string) {
    setReceivingLineDrafts((current) =>
      current.map((line) => (line.product_id === productId ? { ...line, received_quantity: value } : line)),
    );
  }

  function setReceivingLineDiscrepancyNote(productId: string, value: string) {
    setReceivingLineDrafts((current) =>
      current.map((line) => (line.product_id === productId ? { ...line, discrepancy_note: value } : line)),
    );
  }

  async function startSession() {
    setIsBusy(true);
    setErrorMessage('');
    try {
      const session = await ownerControlPlaneClient.exchangeSession(korsenexToken);
      const nextActor = await ownerControlPlaneClient.getActor(session.access_token);
      const nextTenantId = nextActor.tenant_memberships[0]?.tenant_id;
      if (!nextTenantId) {
        throw new Error('Owner session is not bound to a tenant');
      }
      const [tenantSummary, branchList, tenantAudit] = await Promise.all([
        ownerControlPlaneClient.getTenantSummary(session.access_token, nextTenantId),
        ownerControlPlaneClient.listBranches(session.access_token, nextTenantId),
        ownerControlPlaneClient.listAuditEvents(session.access_token, nextTenantId),
      ]);
      const staffDirectory = await ownerControlPlaneClient.listStaffProfiles(session.access_token, nextTenantId);
      const productCatalog = await ownerControlPlaneClient.listCatalogProducts(session.access_token, nextTenantId);
      const branchCatalog =
        branchList.records[0] == null
          ? { records: [] }
          : await ownerControlPlaneClient.listBranchCatalogItems(session.access_token, nextTenantId, branchList.records[0].branch_id);
      const deviceList =
        branchList.records[0] == null
          ? { records: [] }
          : await ownerControlPlaneClient.listBranchDevices(session.access_token, nextTenantId, branchList.records[0].branch_id);
      const supplierDirectory = await ownerControlPlaneClient.listSuppliers(session.access_token, nextTenantId);
      startTransition(() => {
        setAccessToken(session.access_token);
        setActor(nextActor);
        setTenant(tenantSummary);
        setBranches(branchList.records);
        setTransferDestinationBranchId(branchList.records[1]?.branch_id ?? '');
        setCatalogProducts(productCatalog.records);
        setBranchCatalogItems(branchCatalog.records);
        setStaffProfiles(staffDirectory.records);
        setDevices(deviceList.records);
        setSuppliers(supplierDirectory.records);
        setAuditEvents(tenantAudit.records);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to start owner session');
    } finally {
      setIsBusy(false);
    }
  }

  async function createFirstBranch() {
    if (!accessToken || !tenantId) {
      return;
    }
    await runCreateFirstBranch({
      accessToken,
      tenantId,
      name: branchName,
      code: branchCode,
      gstin: branchGstin,
      setIsBusy,
      setErrorMessage,
      setTenant,
      setBranches,
      setTransferDestinationBranchId,
      setCatalogProducts,
      setBranchCatalogItems,
      setDevices,
      resetForm: () => {
        setBranchName('');
        setBranchCode('');
        setBranchGstin('');
      },
    });
  }

  async function assignTenantRole() {
    if (!accessToken || !tenantId) {
      return;
    }
    await runAssignTenantRole({
      accessToken,
      tenantId,
      email: tenantStaffEmail,
      fullName: tenantStaffFullName,
      setIsBusy,
      setErrorMessage,
      setLatestTenantMembership,
      setStaffProfiles,
      resetForm: () => {
        setTenantStaffEmail('');
        setTenantStaffFullName('');
      },
    });
  }

  async function assignBranchRole() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    await runAssignBranchRole({
      accessToken,
      tenantId,
      branchId,
      email: branchStaffEmail,
      fullName: branchStaffFullName,
      setIsBusy,
      setErrorMessage,
      setLatestBranchMembership,
      setStaffProfiles,
      resetForm: () => {
        setBranchStaffEmail('');
        setBranchStaffFullName('');
      },
    });
  }

  async function createStaffProfile() {
    if (!accessToken || !tenantId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const profile = await ownerControlPlaneClient.createStaffProfile(accessToken, tenantId, {
        email: staffProfileEmail,
        full_name: staffProfileFullName,
        phone_number: staffProfilePhone || null,
        primary_branch_id: branchId || null,
      });
      const staffDirectory = await ownerControlPlaneClient.listStaffProfiles(accessToken, tenantId);
      startTransition(() => {
        setLatestStaffProfile(profile);
        setStaffProfiles(staffDirectory.records);
        setStaffProfileEmail('');
        setStaffProfileFullName('');
        setStaffProfilePhone('');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to create staff profile');
    } finally {
      setIsBusy(false);
    }
  }

  async function createCatalogProduct() {
    if (!accessToken || !tenantId) {
      return;
    }
    await runCreateCatalogProduct({
      accessToken,
      tenantId,
      name: productName,
      skuCode: productSkuCode,
      barcode: productBarcode,
      hsnSacCode: productHsnSacCode,
      gstRate: Number(productGstRate),
      sellingPrice: Number(productSellingPrice),
      setIsBusy,
      setErrorMessage,
      setLatestCatalogProduct,
      setCatalogProducts,
      resetForm: () => {
        setProductName('');
        setProductSkuCode('');
        setProductBarcode('');
        setProductHsnSacCode('');
        setProductGstRate('5');
        setProductSellingPrice('');
      },
    });
  }

  async function assignFirstProductToBranch() {
    if (!accessToken || !tenantId || !branchId || !catalogProducts[0]) {
      return;
    }
    await runAssignFirstProductToBranch({
      accessToken,
      tenantId,
      branchId,
      productId: catalogProducts[0].product_id,
      sellingPriceOverride: branchCatalogPriceOverride,
      setIsBusy,
      setErrorMessage,
      setLatestBranchCatalogItem,
      setBranchCatalogItems,
      setBranchCatalogPriceOverride,
    });
  }

  async function allocateFirstProductBarcode() {
    if (!accessToken || !tenantId || !branchId || !catalogProducts[0]) {
      return;
    }
    await runAllocateCatalogBarcode({
      accessToken,
      tenantId,
      branchId,
      productId: catalogProducts[0].product_id,
      manualBarcode: barcodeManualValue,
      setIsBusy,
      setErrorMessage,
      setLatestBarcodeAllocation,
      setCatalogProducts,
      setBranchCatalogItems,
      setBarcodeManualValue,
    });
  }

  async function previewFirstProductBarcodeLabel() {
    if (!accessToken || !tenantId || !branchId || !catalogProducts[0]) {
      return;
    }
    await runPreviewBarcodeLabel({
      accessToken,
      tenantId,
      branchId,
      productId: catalogProducts[0].product_id,
      setIsBusy,
      setErrorMessage,
      setLatestBarcodeLabelPreview,
    });
  }

  async function registerBranchDevice() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    await runRegisterBranchDevice({
      accessToken,
      tenantId,
      branchId,
      deviceName,
      deviceCode,
      assignedStaffProfileId: staffProfiles[0]?.id ?? null,
      setIsBusy,
      setErrorMessage,
      setLatestDevice,
      setDevices,
      resetForm: () => {
        setDeviceName('');
        setDeviceCode('');
      },
    });
  }

  async function createSupplier() {
    if (!accessToken || !tenantId) {
      return;
    }
    await runCreateSupplier({
      accessToken,
      tenantId,
      name: supplierName,
      gstin: supplierGstin,
      paymentTermsDays: supplierPaymentTermsDays,
      setIsBusy,
      setErrorMessage,
      setLatestSupplier,
      setSuppliers,
      resetForm: () => {
        setSupplierName('');
        setSupplierGstin('');
        setSupplierPaymentTermsDays('14');
      },
    });
  }

  async function createPurchaseOrder() {
    if (!accessToken || !tenantId || !branchId || !suppliers[0] || !catalogProducts[0]) {
      return;
    }
    await runCreatePurchaseOrder({
      accessToken,
      tenantId,
      branchId,
      supplierId: suppliers[0].supplier_id,
      productId: catalogProducts[0].product_id,
      purchaseQuantity,
      purchaseUnitCost,
      setIsBusy,
      setErrorMessage,
      setLatestPurchaseOrder,
      setPurchaseOrders,
      setPurchaseApprovalReport,
      setLatestApprovalState,
      resetForm: () => {
        setPurchaseQuantity('');
        setPurchaseUnitCost('');
      },
    });
  }

  async function submitPurchaseOrder() {
    if (!accessToken || !tenantId || !branchId || !latestPurchaseOrder) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const purchaseOrder = await ownerControlPlaneClient.submitPurchaseOrderApproval(accessToken, tenantId, branchId, latestPurchaseOrder.id, {
        note: approvalNote || null,
      });
      const [purchaseOrderList, report] = await Promise.all([
        ownerControlPlaneClient.listPurchaseOrders(accessToken, tenantId, branchId),
        ownerControlPlaneClient.getPurchaseApprovalReport(accessToken, tenantId, branchId),
      ]);
      startTransition(() => {
        setLatestPurchaseOrder(purchaseOrder);
        setPurchaseOrders(purchaseOrderList.records);
        setPurchaseApprovalReport(report);
        setLatestApprovalState(report.records[0] ?? null);
        setApprovalNote('');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to submit purchase order');
    } finally {
      setIsBusy(false);
    }
  }

  async function approvePurchaseOrder() {
    if (!accessToken || !tenantId || !branchId || !latestPurchaseOrder) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const purchaseOrder = await ownerControlPlaneClient.approvePurchaseOrder(accessToken, tenantId, branchId, latestPurchaseOrder.id, {
        note: decisionNote || null,
      });
      const [purchaseOrderList, report] = await Promise.all([
        ownerControlPlaneClient.listPurchaseOrders(accessToken, tenantId, branchId),
        ownerControlPlaneClient.getPurchaseApprovalReport(accessToken, tenantId, branchId),
      ]);
      startTransition(() => {
        setLatestPurchaseOrder(purchaseOrder);
        setPurchaseOrders(purchaseOrderList.records);
        setPurchaseApprovalReport(report);
        setLatestApprovalState(report.records[0] ?? null);
        setDecisionNote('');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to approve purchase order');
    } finally {
      setIsBusy(false);
    }
  }

  async function createGoodsReceipt() {
    if (!accessToken || !tenantId || !branchId || !latestPurchaseOrder) {
      return;
    }
    await runCreateGoodsReceipt({
      accessToken,
      tenantId,
      branchId,
      purchaseOrderId: latestPurchaseOrder.id,
      note: goodsReceiptNote,
      lines: receivingLineDrafts.map((line) => ({
        product_id: line.product_id,
        received_quantity: Number(line.received_quantity),
        discrepancy_note: line.discrepancy_note,
      })),
      setIsBusy,
      setErrorMessage,
      setLatestGoodsReceipt,
      setGoodsReceipts,
      setReceivingBoard,
      setInventoryLedger,
      setInventorySnapshot,
      resetForm: () => {
        setGoodsReceiptNote('');
        setReceivingLineDrafts(
          latestPurchaseOrder.lines.map((line) => ({
            product_id: line.product_id,
            received_quantity: String(line.quantity),
            discrepancy_note: '',
          })),
        );
      },
    });
  }

  async function createPurchaseInvoice() {
    if (!accessToken || !tenantId || !branchId || !latestGoodsReceipt) {
      return;
    }
    await runCreatePurchaseInvoice({
      accessToken,
      tenantId,
      branchId,
      goodsReceiptId: latestGoodsReceipt.id,
      setIsBusy,
      setErrorMessage,
      setLatestPurchaseInvoice,
      setPurchaseInvoices,
      setSupplierPayablesReport,
    });
  }

  async function createSupplierReturn() {
    const returnableLine = latestPurchaseInvoice?.lines[0];
    if (!accessToken || !tenantId || !branchId || !latestPurchaseInvoice || !returnableLine) {
      return;
    }
    await runCreateSupplierReturn({
      accessToken,
      tenantId,
      branchId,
      purchaseInvoiceId: latestPurchaseInvoice.id,
      productId: returnableLine.product_id,
      quantity: Number(supplierReturnQuantity),
      setIsBusy,
      setErrorMessage,
      setLatestSupplierReturn,
      setSupplierPayablesReport,
      setInventoryLedger,
      setInventorySnapshot,
      setSupplierReturnQuantity,
    });
  }

  async function createSupplierPayment() {
    if (!accessToken || !tenantId || !branchId || !latestPurchaseInvoice) {
      return;
    }
    await runCreateSupplierPayment({
      accessToken,
      tenantId,
      branchId,
      purchaseInvoiceId: latestPurchaseInvoice.id,
      amount: Number(supplierPaymentAmount),
      paymentMethod: supplierPaymentMethod,
      reference: supplierPaymentReference,
      setIsBusy,
      setErrorMessage,
      setLatestSupplierPayment,
      setSupplierPayablesReport,
      setSupplierPaymentAmount,
      setSupplierPaymentReference,
    });
  }

  async function createStockAdjustment() {
    const productId = inventorySnapshot[0]?.product_id ?? catalogProducts[0]?.product_id;
    if (!accessToken || !tenantId || !branchId || !productId) {
      return;
    }
    await runCreateStockAdjustment({
      accessToken,
      tenantId,
      branchId,
      productId,
      quantityDelta: Number(adjustmentDelta),
      reason: adjustmentReason,
      setIsBusy,
      setErrorMessage,
      setLatestStockAdjustment,
      setInventoryLedger,
      setInventorySnapshot,
      resetForm: () => {
        setAdjustmentDelta('');
        setAdjustmentReason('');
      },
    });
  }

  async function createStockCountSession() {
    const productId = inventorySnapshot[0]?.product_id ?? catalogProducts[0]?.product_id;
    if (!accessToken || !tenantId || !branchId || !productId) {
      return;
    }
    await runCreateStockCountSession({
      accessToken,
      tenantId,
      branchId,
      productId,
      note: countNote,
      setIsBusy,
      setErrorMessage,
      setLatestStockCountSession,
      setStockCountBoard,
    });
  }

  async function recordStockCountSession() {
    if (!accessToken || !tenantId || !branchId || !latestStockCountSession) {
      return;
    }
    await runRecordStockCountSession({
      accessToken,
      tenantId,
      branchId,
      stockCountSessionId: latestStockCountSession.id,
      countedQuantity: Number(blindCountedQuantity),
      note: countNote,
      setIsBusy,
      setErrorMessage,
      setLatestStockCountSession,
      setStockCountBoard,
      resetForm: () => {
        setBlindCountedQuantity('');
      },
    });
  }

  async function approveStockCountSession() {
    if (!accessToken || !tenantId || !branchId || !latestStockCountSession) {
      return;
    }
    await runApproveStockCountSession({
      accessToken,
      tenantId,
      branchId,
      stockCountSessionId: latestStockCountSession.id,
      reviewNote: stockCountReviewNote,
      setIsBusy,
      setErrorMessage,
      setLatestStockCountSession,
      setLatestStockCount,
      setStockCountBoard,
      setInventoryLedger,
      setInventorySnapshot,
    });
  }

  async function cancelStockCountSession() {
    if (!accessToken || !tenantId || !branchId || !latestStockCountSession) {
      return;
    }
    await runCancelStockCountSession({
      accessToken,
      tenantId,
      branchId,
      stockCountSessionId: latestStockCountSession.id,
      reviewNote: stockCountReviewNote,
      setIsBusy,
      setErrorMessage,
      setLatestStockCountSession,
      setStockCountBoard,
    });
  }

  async function createBranchTransfer() {
    const productId = inventorySnapshot[0]?.product_id ?? catalogProducts[0]?.product_id;
    if (!accessToken || !tenantId || !branchId || !productId || !transferDestinationBranchId) {
      return;
    }
    await runCreateBranchTransfer({
      accessToken,
      tenantId,
      branchId,
      destinationBranchId: transferDestinationBranchId,
      productId,
      quantity: Number(transferQuantity),
      setIsBusy,
      setErrorMessage,
      setLatestTransfer,
      setTransferBoard,
      setInventoryLedger,
      setInventorySnapshot,
      resetForm: () => {
        setTransferQuantity('');
      },
    });
  }

  async function recordBatchLotsOnLatestGoodsReceipt() {
    const productId = catalogProducts[0]?.product_id;
    if (!accessToken || !tenantId || !branchId || !productId) {
      return;
    }
    await runRecordBatchLotsOnLatestGoodsReceipt({
      accessToken,
      tenantId,
      branchId,
      productId,
      lotA: {
        batchNumber: lotABatchNumber,
        quantity: lotAQuantity,
        expiryDate: lotAExpiryDate,
      },
      lotB: {
        batchNumber: lotBBatchNumber,
        quantity: lotBQuantity,
        expiryDate: lotBExpiryDate,
      },
      setIsBusy,
      setErrorMessage,
      setGoodsReceipts,
      setLatestBatchLotIntake,
      setBatchExpiryReport,
      resetForm: () => {
        setLotABatchNumber('');
        setLotAQuantity('');
        setLotAExpiryDate('');
        setLotBBatchNumber('');
        setLotBQuantity('');
        setLotBExpiryDate('');
      },
    });
  }

  async function loadBatchExpiryReport() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    await runLoadBatchExpiryReport({
      accessToken,
      tenantId,
      branchId,
      setIsBusy,
      setErrorMessage,
      setBatchExpiryReport,
    });
  }

  async function createBatchExpirySession() {
    const firstBatchRecord = batchExpiryReport?.records[0];
    if (!accessToken || !tenantId || !branchId || !firstBatchRecord) {
      return;
    }
    await runCreateBatchExpirySession({
      accessToken,
      tenantId,
      branchId,
      batchLotId: firstBatchRecord.batch_lot_id,
      note: expirySessionNote,
      setIsBusy,
      setErrorMessage,
      setLatestBatchExpirySession,
      setBatchExpiryBoard,
    });
  }

  async function recordBatchExpirySession() {
    if (!accessToken || !tenantId || !branchId || !latestBatchExpirySession) {
      return;
    }
    await runRecordBatchExpirySession({
      accessToken,
      tenantId,
      branchId,
      batchExpirySessionId: latestBatchExpirySession.id,
      quantity: expiryWriteOffQuantity,
      reason: expiryWriteOffReason,
      setIsBusy,
      setErrorMessage,
      setLatestBatchExpirySession,
      setBatchExpiryBoard,
    });
  }

  async function approveBatchExpirySession() {
    if (!accessToken || !tenantId || !branchId || !latestBatchExpirySession) {
      return;
    }
    await runApproveBatchExpirySession({
      accessToken,
      tenantId,
      branchId,
      batchExpirySessionId: latestBatchExpirySession.id,
      reviewNote: expiryReviewNote,
      setIsBusy,
      setErrorMessage,
      setLatestBatchExpirySession,
      setLatestBatchExpiryWriteOff,
      setBatchExpiryBoard,
      setBatchExpiryReport,
      setInventoryLedger,
      setInventorySnapshot,
    });
  }

  async function cancelBatchExpirySession() {
    if (!accessToken || !tenantId || !branchId || !latestBatchExpirySession) {
      return;
    }
    await runCancelBatchExpirySession({
      accessToken,
      tenantId,
      branchId,
      batchExpirySessionId: latestBatchExpirySession.id,
      reviewNote: expiryReviewNote,
      setIsBusy,
      setErrorMessage,
      setLatestBatchExpirySession,
      setBatchExpiryBoard,
    });
  }

  async function loadReplenishmentBoard() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    await runLoadReplenishmentBoard({
      accessToken,
      tenantId,
      branchId,
      setIsBusy,
      setErrorMessage,
      setReplenishmentBoard,
    });
  }

  async function updateFirstBranchReplenishmentPolicy() {
    if (!accessToken || !tenantId || !branchId || !branchCatalogItems[0]) {
      return;
    }
    await runUpdateFirstBranchReplenishmentPolicy({
      accessToken,
      tenantId,
      branchId,
      branchCatalogItem: branchCatalogItems[0],
      reorderPoint: replenishmentReorderPoint,
      targetStock: replenishmentTargetStock,
      setIsBusy,
      setErrorMessage,
      setLatestBranchCatalogItem,
      setReplenishmentBoard,
    });
  }

  async function loadRestockBoard() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    await runLoadRestockBoard({
      accessToken,
      tenantId,
      branchId,
      setIsBusy,
      setErrorMessage,
      setRestockBoard,
    });
  }

  async function createRestockTask() {
    const lowStockRecord = replenishmentBoard?.records.find((record) => record.replenishment_status === 'LOW_STOCK');
    if (!accessToken || !tenantId || !branchId || !lowStockRecord) {
      return;
    }
    await runCreateRestockTask({
      accessToken,
      tenantId,
      branchId,
      productId: lowStockRecord.product_id,
      requestedQuantity: Number(restockRequestedQuantity),
      sourcePosture: restockSourcePosture,
      note: restockNote,
      setIsBusy,
      setErrorMessage,
      setLatestRestockTask,
      setRestockBoard,
      resetForm: () => {
        setRestockRequestedQuantity('');
        setRestockNote('');
      },
    });
  }

  async function pickRestockTask() {
    if (!accessToken || !tenantId || !branchId || !latestRestockTask) {
      return;
    }
    await runPickRestockTask({
      accessToken,
      tenantId,
      branchId,
      restockTaskId: latestRestockTask.id,
      pickedQuantity: Number(restockPickedQuantity),
      note: restockNote,
      setIsBusy,
      setErrorMessage,
      setLatestRestockTask,
      setRestockBoard,
      resetForm: () => {
        setRestockPickedQuantity('');
      },
    });
  }

  async function completeRestockTask() {
    if (!accessToken || !tenantId || !branchId || !latestRestockTask) {
      return;
    }
    await runCompleteRestockTask({
      accessToken,
      tenantId,
      branchId,
      restockTaskId: latestRestockTask.id,
      completionNote: restockCompletionNote,
      setIsBusy,
      setErrorMessage,
      setLatestRestockTask,
      setRestockBoard,
      resetForm: () => {
        setRestockCompletionNote('');
      },
    });
  }

  async function cancelRestockTask() {
    if (!accessToken || !tenantId || !branchId || !latestRestockTask) {
      return;
    }
    await runCancelRestockTask({
      accessToken,
      tenantId,
      branchId,
      restockTaskId: latestRestockTask.id,
      cancelNote: restockCompletionNote,
      setIsBusy,
      setErrorMessage,
      setLatestRestockTask,
      setRestockBoard,
      resetForm: () => {
        setRestockCompletionNote('');
      },
    });
  }

  return {
    accessToken,
    allocateFirstProductBarcode,
    adjustmentDelta,
    adjustmentReason,
    approvalNote,
    approveBatchExpirySession,
    approvePurchaseOrder,
    actor,
    auditEvents,
    assignFirstProductToBranch,
    batchExpiryBoard,
    batchExpiryReport,
    branches,
    barcodeManualValue,
    branchCatalogItems,
    branchCatalogPriceOverride,
    createStaffProfile,
    createCatalogProduct,
    createSupplier,
    createPurchaseOrder,
    createGoodsReceipt,
    createBatchExpirySession,
    recordBatchLotsOnLatestGoodsReceipt,
    createPurchaseInvoice,
    createSupplierPayment,
    createSupplierReturn,
    createStockAdjustment,
    createStockCountSession,
    recordStockCountSession,
    approveStockCountSession,
    cancelStockCountSession,
    createBranchTransfer,
    blindCountedQuantity,
    branchCode,
    branchGstin,
    branchId,
    branchName,
    catalogProducts,
    decisionNote,
    deviceCode,
    deviceName,
    devices,
    goodsReceipts,
    countedQuantity,
    countNote,
    stockCountReviewNote,
    expirySessionNote,
    expiryReviewNote,
    expiryWriteOffQuantity,
    expiryWriteOffReason,
    branchStaffEmail,
    branchStaffFullName,
    errorMessage,
    goodsReceiptNote,
    receivingLineDrafts,
    isBusy,
    inventoryLedger,
    inventorySnapshot,
    korsenexToken,
    latestApprovalState,
    latestBarcodeAllocation,
    latestBarcodeLabelPreview,
    latestBatchExpirySession,
    latestBatchExpiryWriteOff,
    latestBatchLotIntake,
    latestCatalogProduct,
    latestBranchCatalogItem,
    latestDevice,
    latestGoodsReceipt,
    latestPurchaseInvoice,
    latestPurchaseOrder,
    latestRestockTask,
    loadReplenishmentBoard,
    loadRestockBoard,
    latestStockAdjustment,
    latestStockCount,
    latestStockCountSession,
    latestStaffProfile,
    latestSupplier,
    latestSupplierPayment,
    latestSupplierReturn,
    latestTransfer,
    latestBranchMembership,
    latestTenantMembership,
    purchaseApprovalReport,
    purchaseInvoices,
    purchaseOrders,
    purchaseQuantity,
    purchaseUnitCost,
    replenishmentBoard,
    replenishmentReorderPoint,
    replenishmentTargetStock,
    restockBoard,
    restockCompletionNote,
    restockNote,
    restockPickedQuantity,
    restockRequestedQuantity,
    restockSourcePosture,
    lotABatchNumber,
    lotAExpiryDate,
    lotAQuantity,
    lotBBatchNumber,
    lotBExpiryDate,
    lotBQuantity,
    loadBatchExpiryReport,
    previewFirstProductBarcodeLabel,
    receivingBoard,
    recordBatchExpirySession,
    stockCountBoard,
    registerBranchDevice,
    setAdjustmentDelta,
    setAdjustmentReason,
    setApprovalNote,
    setBarcodeManualValue,
    setBlindCountedQuantity,
    setDeviceCode,
    setDeviceName,
    setBranchCatalogPriceOverride,
    setDecisionNote,
    setCountedQuantity,
    setCountNote,
    setStockCountReviewNote,
    setExpirySessionNote,
    setExpiryReviewNote,
    setExpiryWriteOffQuantity,
    setExpiryWriteOffReason,
    setGoodsReceiptNote,
    setLotABatchNumber,
    setLotAExpiryDate,
    setLotAQuantity,
    setLotBBatchNumber,
    setLotBExpiryDate,
    setLotBQuantity,
    setReceivingLineDiscrepancyNote,
    setReceivingLineQuantity,
    setProductBarcode,
    setProductGstRate,
    setProductHsnSacCode,
    setProductName,
    setProductSellingPrice,
    setProductSkuCode,
    setReplenishmentReorderPoint,
    setReplenishmentTargetStock,
    setRestockCompletionNote,
    setRestockNote,
    setRestockPickedQuantity,
    setRestockRequestedQuantity,
    setRestockSourcePosture,
    setPurchaseQuantity,
    setPurchaseUnitCost,
    setStaffProfileEmail,
    setStaffProfileFullName,
    setStaffProfilePhone,
    setSupplierGstin,
    setSupplierName,
    setSupplierPaymentTermsDays,
    setSupplierPaymentAmount,
    setSupplierPaymentMethod,
    setSupplierPaymentReference,
    setSupplierReturnQuantity,
    setTransferDestinationBranchId,
    setTransferQuantity,
    submitPurchaseOrder,
    supplierPayablesReport,
    supplierGstin,
    supplierName,
    supplierPaymentAmount,
    supplierPaymentMethod,
    supplierPaymentReference,
    supplierPaymentTermsDays,
    supplierReturnQuantity,
    suppliers,
    tenant,
    tenantId,
    transferBoard,
    transferDestinationBranchId,
    transferQuantity,
    createRestockTask,
    pickRestockTask,
    completeRestockTask,
    cancelRestockTask,
    updateFirstBranchReplenishmentPolicy,
    productBarcode,
    productGstRate,
    productHsnSacCode,
    productName,
    productSellingPrice,
    productSkuCode,
    staffProfileEmail,
    staffProfileFullName,
    staffProfilePhone,
    staffProfiles,
    tenantStaffEmail,
    tenantStaffFullName,
    setBranchCode,
    setBranchGstin,
    setBranchName,
    setBranchStaffEmail,
    setBranchStaffFullName,
    setKorsenexToken,
    setTenantStaffEmail,
    setTenantStaffFullName,
    assignBranchRole,
    assignTenantRole,
    cancelBatchExpirySession,
    createFirstBranch,
    startSession,
  };
}

export type OwnerWorkspaceState = ReturnType<typeof useOwnerWorkspace>;
