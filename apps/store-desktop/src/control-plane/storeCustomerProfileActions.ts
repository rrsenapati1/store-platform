import type { ControlPlaneCustomerProfile } from '@store/types';
import { storeControlPlaneClient } from './client';

type LoadCustomerProfilesArgs = {
  accessToken: string;
  tenantId: string;
  query: string;
};

type CreateCheckoutCustomerProfileArgs = {
  accessToken: string;
  tenantId: string;
  fullName: string;
  gstin?: string | null;
};

export async function runLoadCustomerProfiles({
  accessToken,
  tenantId,
  query,
}: LoadCustomerProfilesArgs): Promise<ControlPlaneCustomerProfile[]> {
  const response = await storeControlPlaneClient.listCustomerProfiles(accessToken, tenantId, query);
  return response.records;
}

export async function runCreateCheckoutCustomerProfile({
  accessToken,
  tenantId,
  fullName,
  gstin,
}: CreateCheckoutCustomerProfileArgs): Promise<ControlPlaneCustomerProfile> {
  return storeControlPlaneClient.createCustomerProfile(accessToken, tenantId, {
    full_name: fullName,
    gstin: gstin ?? null,
  });
}
