import type { ControlPlaneCustomerStoreCredit } from '@store/types';
import { storeControlPlaneClient } from './client';

type LoadCustomerStoreCreditArgs = {
  accessToken: string;
  tenantId: string;
  customerProfileId: string;
};

export async function runLoadCustomerStoreCredit({
  accessToken,
  tenantId,
  customerProfileId,
}: LoadCustomerStoreCreditArgs): Promise<ControlPlaneCustomerStoreCredit> {
  return storeControlPlaneClient.getCustomerStoreCredit(accessToken, tenantId, customerProfileId);
}
