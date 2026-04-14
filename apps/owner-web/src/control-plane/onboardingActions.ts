import { startTransition } from 'react';
import type {
  ControlPlaneBranchCatalogItem,
  ControlPlaneBranchRecord,
  ControlPlaneCatalogProductRecord,
  ControlPlaneDeviceRecord,
  ControlPlaneDeviceRegistration,
  ControlPlaneTenant,
} from '@store/types';
import { ownerControlPlaneClient } from './client';

type SetString = (value: string) => void;

export async function runCreateFirstBranch(params: {
  accessToken: string;
  tenantId: string;
  name: string;
  code: string;
  gstin: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setTenant: (value: ControlPlaneTenant | null) => void;
  setBranches: (value: ControlPlaneBranchRecord[]) => void;
  setTransferDestinationBranchId: SetString;
  setCatalogProducts: (value: ControlPlaneCatalogProductRecord[]) => void;
  setBranchCatalogItems: (value: ControlPlaneBranchCatalogItem[]) => void;
  setDevices: (value: ControlPlaneDeviceRecord[]) => void;
  resetForm: () => void;
}) {
  const {
    accessToken,
    tenantId,
    name,
    code,
    gstin,
    setIsBusy,
    setErrorMessage,
    setTenant,
    setBranches,
    setTransferDestinationBranchId,
    setCatalogProducts,
    setBranchCatalogItems,
    setDevices,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    await ownerControlPlaneClient.createBranch(accessToken, tenantId, {
      name,
      code,
      gstin,
      timezone: 'Asia/Kolkata',
    });
    const [tenantSummary, branchList] = await Promise.all([
      ownerControlPlaneClient.getTenantSummary(accessToken, tenantId),
      ownerControlPlaneClient.listBranches(accessToken, tenantId),
    ]);
    const productCatalog = await ownerControlPlaneClient.listCatalogProducts(accessToken, tenantId);
    const deviceList =
      branchList.records[0] == null
        ? { records: [] }
        : await ownerControlPlaneClient.listBranchDevices(accessToken, tenantId, branchList.records[0].branch_id);
    const branchCatalog =
      branchList.records[0] == null
        ? { records: [] }
        : await ownerControlPlaneClient.listBranchCatalogItems(accessToken, tenantId, branchList.records[0].branch_id);
    startTransition(() => {
      setTenant(tenantSummary);
      setBranches(branchList.records);
      setTransferDestinationBranchId(branchList.records[1]?.branch_id ?? '');
      setCatalogProducts(productCatalog.records);
      setBranchCatalogItems(branchCatalog.records);
      setDevices(deviceList.records);
      resetForm();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to create branch');
  } finally {
    setIsBusy(false);
  }
}

export async function runRegisterBranchDevice(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  deviceName: string;
  deviceCode: string;
  assignedStaffProfileId?: string | null;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestDevice: (value: ControlPlaneDeviceRegistration | null) => void;
  setDevices: (value: ControlPlaneDeviceRecord[]) => void;
  resetForm: () => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    deviceName,
    deviceCode,
    assignedStaffProfileId,
    setIsBusy,
    setErrorMessage,
    setLatestDevice,
    setDevices,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const device = await ownerControlPlaneClient.registerBranchDevice(accessToken, tenantId, branchId, {
      device_name: deviceName,
      device_code: deviceCode,
      session_surface: 'store_desktop',
      assigned_staff_profile_id: assignedStaffProfileId ?? null,
    });
    const deviceList = await ownerControlPlaneClient.listBranchDevices(accessToken, tenantId, branchId);
    startTransition(() => {
      setLatestDevice(device);
      setDevices(deviceList.records);
      resetForm();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to register branch device');
  } finally {
    setIsBusy(false);
  }
}
