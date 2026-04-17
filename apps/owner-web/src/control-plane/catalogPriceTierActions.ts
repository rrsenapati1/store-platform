import { startTransition } from 'react';
import type { ControlPlaneBranchPriceTierPrice, ControlPlanePriceTier } from '@store/types';
import { ownerControlPlaneClient } from './client';

type SetString = (value: string) => void;

export async function runLoadPriceTiers(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setPriceTiers: (value: ControlPlanePriceTier[]) => void;
  setBranchPriceTierPrices: (value: ControlPlaneBranchPriceTierPrice[]) => void;
}) {
  const { accessToken, tenantId, branchId, setIsBusy, setErrorMessage, setPriceTiers, setBranchPriceTierPrices } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const [priceTiers, branchTierPrices] = await Promise.all([
      ownerControlPlaneClient.listPriceTiers(accessToken, tenantId),
      ownerControlPlaneClient.listBranchPriceTierPrices(accessToken, tenantId, branchId),
    ]);
    startTransition(() => {
      setPriceTiers(priceTiers.records);
      setBranchPriceTierPrices(branchTierPrices.records);
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to load price tiers');
  } finally {
    setIsBusy(false);
  }
}

export async function runCreatePriceTier(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  code: string;
  displayName: string;
  status: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestPriceTier: (value: ControlPlanePriceTier | null) => void;
  setPriceTiers: (value: ControlPlanePriceTier[]) => void;
  setBranchPriceTierPrices: (value: ControlPlaneBranchPriceTierPrice[]) => void;
  resetForm: () => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    code,
    displayName,
    status,
    setIsBusy,
    setErrorMessage,
    setLatestPriceTier,
    setPriceTiers,
    setBranchPriceTierPrices,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const created = await ownerControlPlaneClient.createPriceTier(accessToken, tenantId, {
      code,
      display_name: displayName,
      status,
    });
    const [priceTiers, branchTierPrices] = await Promise.all([
      ownerControlPlaneClient.listPriceTiers(accessToken, tenantId),
      ownerControlPlaneClient.listBranchPriceTierPrices(accessToken, tenantId, branchId),
    ]);
    startTransition(() => {
      setLatestPriceTier(created);
      setPriceTiers(priceTiers.records);
      setBranchPriceTierPrices(branchTierPrices.records);
      resetForm();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to create price tier');
  } finally {
    setIsBusy(false);
  }
}

export async function runUpsertBranchPriceTierPrice(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  productId: string;
  priceTierId: string;
  sellingPrice: number;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestBranchPriceTierPrice: (value: ControlPlaneBranchPriceTierPrice | null) => void;
  setBranchPriceTierPrices: (value: ControlPlaneBranchPriceTierPrice[]) => void;
  resetForm: () => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    productId,
    priceTierId,
    sellingPrice,
    setIsBusy,
    setErrorMessage,
    setLatestBranchPriceTierPrice,
    setBranchPriceTierPrices,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const created = await ownerControlPlaneClient.upsertBranchPriceTierPrice(accessToken, tenantId, branchId, {
      product_id: productId,
      price_tier_id: priceTierId,
      selling_price: sellingPrice,
    });
    const branchTierPrices = await ownerControlPlaneClient.listBranchPriceTierPrices(accessToken, tenantId, branchId);
    startTransition(() => {
      setLatestBranchPriceTierPrice(created);
      setBranchPriceTierPrices(branchTierPrices.records);
      resetForm();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to set branch price tier price');
  } finally {
    setIsBusy(false);
  }
}
