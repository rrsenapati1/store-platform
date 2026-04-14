import { startTransition } from 'react';
import type {
  ControlPlanePurchaseInvoice,
  ControlPlanePurchaseInvoiceRecord,
  ControlPlaneSupplierPayablesReport,
  ControlPlaneSupplierPayment,
  ControlPlaneSupplierReturn,
  ControlPlaneInventoryLedgerRecord,
  ControlPlaneInventorySnapshotRecord,
} from '@store/types';
import { ownerControlPlaneClient } from './client';

type SetString = (value: string) => void;

export async function runCreatePurchaseInvoice(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  goodsReceiptId: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestPurchaseInvoice: (value: ControlPlanePurchaseInvoice | null) => void;
  setPurchaseInvoices: (value: ControlPlanePurchaseInvoiceRecord[]) => void;
  setSupplierPayablesReport: (value: ControlPlaneSupplierPayablesReport | null) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    goodsReceiptId,
    setIsBusy,
    setErrorMessage,
    setLatestPurchaseInvoice,
    setPurchaseInvoices,
    setSupplierPayablesReport,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const purchaseInvoice = await ownerControlPlaneClient.createPurchaseInvoice(accessToken, tenantId, branchId, {
      goods_receipt_id: goodsReceiptId,
    });
    const [purchaseInvoiceList, payables] = await Promise.all([
      ownerControlPlaneClient.listPurchaseInvoices(accessToken, tenantId, branchId),
      ownerControlPlaneClient.getSupplierPayablesReport(accessToken, tenantId, branchId),
    ]);
    startTransition(() => {
      setLatestPurchaseInvoice(purchaseInvoice);
      setPurchaseInvoices(purchaseInvoiceList.records);
      setSupplierPayablesReport(payables);
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to create purchase invoice');
  } finally {
    setIsBusy(false);
  }
}

export async function runCreateSupplierReturn(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  purchaseInvoiceId: string;
  productId: string;
  quantity: number;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestSupplierReturn: (value: ControlPlaneSupplierReturn | null) => void;
  setSupplierPayablesReport: (value: ControlPlaneSupplierPayablesReport | null) => void;
  setInventoryLedger: (value: ControlPlaneInventoryLedgerRecord[]) => void;
  setInventorySnapshot: (value: ControlPlaneInventorySnapshotRecord[]) => void;
  setSupplierReturnQuantity: SetString;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    purchaseInvoiceId,
    productId,
    quantity,
    setIsBusy,
    setErrorMessage,
    setLatestSupplierReturn,
    setSupplierPayablesReport,
    setInventoryLedger,
    setInventorySnapshot,
    setSupplierReturnQuantity,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const supplierReturn = await ownerControlPlaneClient.createSupplierReturn(accessToken, tenantId, branchId, purchaseInvoiceId, {
      lines: [{ product_id: productId, quantity }],
    });
    const [payables, ledger, snapshot] = await Promise.all([
      ownerControlPlaneClient.getSupplierPayablesReport(accessToken, tenantId, branchId),
      ownerControlPlaneClient.listInventoryLedger(accessToken, tenantId, branchId),
      ownerControlPlaneClient.listInventorySnapshot(accessToken, tenantId, branchId),
    ]);
    startTransition(() => {
      setLatestSupplierReturn(supplierReturn);
      setSupplierPayablesReport(payables);
      setInventoryLedger(ledger.records);
      setInventorySnapshot(snapshot.records);
      setSupplierReturnQuantity('');
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to create supplier return');
  } finally {
    setIsBusy(false);
  }
}

export async function runCreateSupplierPayment(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  purchaseInvoiceId: string;
  amount: number;
  paymentMethod: string;
  reference: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestSupplierPayment: (value: ControlPlaneSupplierPayment | null) => void;
  setSupplierPayablesReport: (value: ControlPlaneSupplierPayablesReport | null) => void;
  setSupplierPaymentAmount: SetString;
  setSupplierPaymentReference: SetString;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    purchaseInvoiceId,
    amount,
    paymentMethod,
    reference,
    setIsBusy,
    setErrorMessage,
    setLatestSupplierPayment,
    setSupplierPayablesReport,
    setSupplierPaymentAmount,
    setSupplierPaymentReference,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const supplierPayment = await ownerControlPlaneClient.createSupplierPayment(accessToken, tenantId, branchId, purchaseInvoiceId, {
      amount,
      payment_method: paymentMethod,
      reference: reference || null,
    });
    const payables = await ownerControlPlaneClient.getSupplierPayablesReport(accessToken, tenantId, branchId);
    startTransition(() => {
      setLatestSupplierPayment(supplierPayment);
      setSupplierPayablesReport(payables);
      setSupplierPaymentAmount('');
      setSupplierPaymentReference('');
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to record supplier payment');
  } finally {
    setIsBusy(false);
  }
}
