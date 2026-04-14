import { startTransition } from 'react';
import type {
  ControlPlanePurchaseApprovalReport,
  ControlPlanePurchaseApprovalReportRecord,
  ControlPlanePurchaseOrder,
  ControlPlanePurchaseOrderRecord,
  ControlPlaneSupplier,
  ControlPlaneSupplierRecord,
} from '@store/types';
import { ownerControlPlaneClient } from './client';

type SetString = (value: string) => void;

export async function runCreateSupplier(params: {
  accessToken: string;
  tenantId: string;
  name: string;
  gstin: string;
  paymentTermsDays: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestSupplier: (value: ControlPlaneSupplier | null) => void;
  setSuppliers: (value: ControlPlaneSupplierRecord[]) => void;
  resetForm: () => void;
}) {
  const {
    accessToken,
    tenantId,
    name,
    gstin,
    paymentTermsDays,
    setIsBusy,
    setErrorMessage,
    setLatestSupplier,
    setSuppliers,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const supplier = await ownerControlPlaneClient.createSupplier(accessToken, tenantId, {
      name,
      gstin: gstin || null,
      payment_terms_days: Number(paymentTermsDays || '0'),
    });
    const supplierDirectory = await ownerControlPlaneClient.listSuppliers(accessToken, tenantId);
    startTransition(() => {
      setLatestSupplier(supplier);
      setSuppliers(supplierDirectory.records);
      resetForm();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to create supplier');
  } finally {
    setIsBusy(false);
  }
}

export async function runCreatePurchaseOrder(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  supplierId: string;
  productId: string;
  purchaseQuantity: string;
  purchaseUnitCost: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestPurchaseOrder: (value: ControlPlanePurchaseOrder | null) => void;
  setPurchaseOrders: (value: ControlPlanePurchaseOrderRecord[]) => void;
  setPurchaseApprovalReport: (value: ControlPlanePurchaseApprovalReport | null) => void;
  setLatestApprovalState: (value: ControlPlanePurchaseApprovalReportRecord | null) => void;
  resetForm: () => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    supplierId,
    productId,
    purchaseQuantity,
    purchaseUnitCost,
    setIsBusy,
    setErrorMessage,
    setLatestPurchaseOrder,
    setPurchaseOrders,
    setPurchaseApprovalReport,
    setLatestApprovalState,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const purchaseOrder = await ownerControlPlaneClient.createPurchaseOrder(accessToken, tenantId, branchId, {
      supplier_id: supplierId,
      lines: [
        {
          product_id: productId,
          quantity: Number(purchaseQuantity),
          unit_cost: Number(purchaseUnitCost),
        },
      ],
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
      resetForm();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to create purchase order');
  } finally {
    setIsBusy(false);
  }
}
