import { normalizeScannedBarcode } from '@store/barcode';
import { startTransition } from 'react';
import type {
  ControlPlaneBarcodeAllocation,
  ControlPlaneBarcodeLabelPreview,
  ControlPlaneBranchCatalogItem,
  ControlPlaneCatalogProduct,
  ControlPlaneCatalogProductRecord,
} from '@store/types';
import { ownerControlPlaneClient } from './client';

type SetString = (value: string) => void;

export async function runCreateCatalogProduct(params: {
  accessToken: string;
  tenantId: string;
  name: string;
  skuCode: string;
  barcode: string;
  hsnSacCode: string;
  gstRate: number;
  sellingPrice: number;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestCatalogProduct: (value: ControlPlaneCatalogProduct | null) => void;
  setCatalogProducts: (value: ControlPlaneCatalogProductRecord[]) => void;
  resetForm: () => void;
}) {
  const {
    accessToken,
    tenantId,
    name,
    skuCode,
    barcode,
    hsnSacCode,
    gstRate,
    sellingPrice,
    setIsBusy,
    setErrorMessage,
    setLatestCatalogProduct,
    setCatalogProducts,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const product = await ownerControlPlaneClient.createCatalogProduct(accessToken, tenantId, {
      name,
      sku_code: skuCode,
      barcode,
      hsn_sac_code: hsnSacCode,
      gst_rate: gstRate,
      selling_price: sellingPrice,
    });
    const productCatalog = await ownerControlPlaneClient.listCatalogProducts(accessToken, tenantId);
    startTransition(() => {
      setLatestCatalogProduct(product);
      setCatalogProducts(productCatalog.records);
      resetForm();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to create catalog product');
  } finally {
    setIsBusy(false);
  }
}

export async function runAssignFirstProductToBranch(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  productId: string;
  sellingPriceOverride: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestBranchCatalogItem: (value: ControlPlaneBranchCatalogItem | null) => void;
  setBranchCatalogItems: (value: ControlPlaneBranchCatalogItem[]) => void;
  setBranchCatalogPriceOverride: SetString;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    productId,
    sellingPriceOverride,
    setIsBusy,
    setErrorMessage,
    setLatestBranchCatalogItem,
    setBranchCatalogItems,
    setBranchCatalogPriceOverride,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const item = await ownerControlPlaneClient.upsertBranchCatalogItem(accessToken, tenantId, branchId, {
      product_id: productId,
      selling_price_override: sellingPriceOverride ? Number(sellingPriceOverride) : null,
      availability_status: 'ACTIVE',
    });
    const branchCatalog = await ownerControlPlaneClient.listBranchCatalogItems(accessToken, tenantId, branchId);
    startTransition(() => {
      setLatestBranchCatalogItem(item);
      setBranchCatalogItems(branchCatalog.records);
      setBranchCatalogPriceOverride('');
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to assign branch catalog item');
  } finally {
    setIsBusy(false);
  }
}

export async function runAllocateCatalogBarcode(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  productId: string;
  manualBarcode: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestBarcodeAllocation: (value: ControlPlaneBarcodeAllocation | null) => void;
  setCatalogProducts: (value: ControlPlaneCatalogProductRecord[]) => void;
  setBranchCatalogItems: (value: ControlPlaneBranchCatalogItem[]) => void;
  setBarcodeManualValue: SetString;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    productId,
    manualBarcode,
    setIsBusy,
    setErrorMessage,
    setLatestBarcodeAllocation,
    setCatalogProducts,
    setBranchCatalogItems,
    setBarcodeManualValue,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const allocation = await ownerControlPlaneClient.allocateCatalogProductBarcode(accessToken, tenantId, productId, {
      barcode: normalizeScannedBarcode(manualBarcode) || null,
    });
    const [productCatalog, branchCatalog] = await Promise.all([
      ownerControlPlaneClient.listCatalogProducts(accessToken, tenantId),
      ownerControlPlaneClient.listBranchCatalogItems(accessToken, tenantId, branchId),
    ]);
    startTransition(() => {
      setLatestBarcodeAllocation(allocation);
      setCatalogProducts(productCatalog.records);
      setBranchCatalogItems(branchCatalog.records);
      setBarcodeManualValue('');
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to allocate barcode');
  } finally {
    setIsBusy(false);
  }
}

export async function runPreviewBarcodeLabel(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  productId: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestBarcodeLabelPreview: (value: ControlPlaneBarcodeLabelPreview | null) => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    productId,
    setIsBusy,
    setErrorMessage,
    setLatestBarcodeLabelPreview,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const preview = await ownerControlPlaneClient.getBarcodeLabelPreview(accessToken, tenantId, branchId, productId);
    startTransition(() => {
      setLatestBarcodeLabelPreview(preview);
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to preview barcode label');
  } finally {
    setIsBusy(false);
  }
}
