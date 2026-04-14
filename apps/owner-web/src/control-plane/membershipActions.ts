import { startTransition } from 'react';
import type { ControlPlaneMembership, ControlPlaneStaffProfileRecord } from '@store/types';
import { ownerControlPlaneClient } from './client';

type SetString = (value: string) => void;

export async function runAssignTenantRole(params: {
  accessToken: string;
  tenantId: string;
  email: string;
  fullName: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestTenantMembership: (value: ControlPlaneMembership | null) => void;
  setStaffProfiles: (value: ControlPlaneStaffProfileRecord[]) => void;
  resetForm: () => void;
}) {
  const {
    accessToken,
    tenantId,
    email,
    fullName,
    setIsBusy,
    setErrorMessage,
    setLatestTenantMembership,
    setStaffProfiles,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const membership = await ownerControlPlaneClient.createTenantMembership(accessToken, tenantId, {
      email,
      full_name: fullName,
      role_name: 'inventory_admin',
    });
    const staffDirectory = await ownerControlPlaneClient.listStaffProfiles(accessToken, tenantId);
    startTransition(() => {
      setLatestTenantMembership(membership);
      setStaffProfiles(staffDirectory.records);
      resetForm();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to assign tenant role');
  } finally {
    setIsBusy(false);
  }
}

export async function runAssignBranchRole(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  email: string;
  fullName: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: SetString;
  setLatestBranchMembership: (value: ControlPlaneMembership | null) => void;
  setStaffProfiles: (value: ControlPlaneStaffProfileRecord[]) => void;
  resetForm: () => void;
}) {
  const {
    accessToken,
    tenantId,
    branchId,
    email,
    fullName,
    setIsBusy,
    setErrorMessage,
    setLatestBranchMembership,
    setStaffProfiles,
    resetForm,
  } = params;

  setIsBusy(true);
  setErrorMessage('');
  try {
    const membership = await ownerControlPlaneClient.createBranchMembership(accessToken, tenantId, branchId, {
      email,
      full_name: fullName,
      role_name: 'cashier',
    });
    const staffDirectory = await ownerControlPlaneClient.listStaffProfiles(accessToken, tenantId);
    startTransition(() => {
      setLatestBranchMembership(membership);
      setStaffProfiles(staffDirectory.records);
      resetForm();
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to assign branch role');
  } finally {
    setIsBusy(false);
  }
}
