import type { ControlPlaneCustomerLoyalty, ControlPlaneLoyaltyProgram } from '@store/types';
import { storeControlPlaneClient } from './client';

type LoadLoyaltyProgramArgs = {
  accessToken: string;
  tenantId: string;
};

type LoadCustomerLoyaltyArgs = {
  accessToken: string;
  tenantId: string;
  customerProfileId: string;
};

export async function runLoadLoyaltyProgram({
  accessToken,
  tenantId,
}: LoadLoyaltyProgramArgs): Promise<ControlPlaneLoyaltyProgram> {
  return storeControlPlaneClient.getLoyaltyProgram(accessToken, tenantId);
}

export async function runLoadCustomerLoyalty({
  accessToken,
  tenantId,
  customerProfileId,
}: LoadCustomerLoyaltyArgs): Promise<ControlPlaneCustomerLoyalty> {
  return storeControlPlaneClient.getCustomerLoyalty(accessToken, tenantId, customerProfileId);
}
