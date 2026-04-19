import type {
  ControlPlaneActor,
  ControlPlaneAuditRecord,
  ControlPlaneBranchCatalogItem,
  ControlPlaneBranchRecord,
  ControlPlaneCatalogProductRecord,
  ControlPlaneDeviceRecord,
  ControlPlaneStaffProfileRecord,
  ControlPlaneSupplierRecord,
  ControlPlaneTenant,
} from '@store/types';
import { ownerControlPlaneClient } from './client';

export const OWNER_WEB_SESSION_STORAGE_KEY = 'owner-web.session';

export type OwnerWorkspaceSessionState = 'signed_out' | 'restoring' | 'expired' | 'revoked' | 'ready';

export type OwnerWorkspaceBootstrap = {
  actor: ControlPlaneActor;
  tenant: ControlPlaneTenant;
  branches: ControlPlaneBranchRecord[];
  auditEvents: ControlPlaneAuditRecord[];
  staffProfiles: ControlPlaneStaffProfileRecord[];
  catalogProducts: ControlPlaneCatalogProductRecord[];
  branchCatalogItems: ControlPlaneBranchCatalogItem[];
  devices: ControlPlaneDeviceRecord[];
  suppliers: ControlPlaneSupplierRecord[];
  selectedBranchId: string;
  transferDestinationBranchId: string;
};

export async function loadOwnerWorkspaceBootstrap(accessToken: string): Promise<OwnerWorkspaceBootstrap> {
  const actor = await ownerControlPlaneClient.getActor(accessToken);
  const tenantId = actor.tenant_memberships[0]?.tenant_id;
  if (!tenantId) {
    throw new Error('Owner session is not bound to a tenant');
  }
  const [tenant, branchList, auditEvents, staffProfiles, catalogProducts, suppliers] = await Promise.all([
    ownerControlPlaneClient.getTenantSummary(accessToken, tenantId),
    ownerControlPlaneClient.listBranches(accessToken, tenantId),
    ownerControlPlaneClient.listAuditEvents(accessToken, tenantId),
    ownerControlPlaneClient.listStaffProfiles(accessToken, tenantId),
    ownerControlPlaneClient.listCatalogProducts(accessToken, tenantId),
    ownerControlPlaneClient.listSuppliers(accessToken, tenantId),
  ]);
  const selectedBranchId = branchList.records[0]?.branch_id ?? '';
  const transferDestinationBranchId = branchList.records[1]?.branch_id ?? '';
  const [branchCatalogItems, devices] = selectedBranchId
    ? await Promise.all([
        ownerControlPlaneClient.listBranchCatalogItems(accessToken, tenantId, selectedBranchId),
        ownerControlPlaneClient.listBranchDevices(accessToken, tenantId, selectedBranchId),
      ])
    : [{ records: [] }, { records: [] }];

  return {
    actor,
    auditEvents: auditEvents.records,
    branchCatalogItems: branchCatalogItems.records,
    branches: branchList.records,
    catalogProducts: catalogProducts.records,
    devices: devices.records,
    selectedBranchId,
    staffProfiles: staffProfiles.records,
    suppliers: suppliers.records,
    tenant,
    transferDestinationBranchId,
  };
}
