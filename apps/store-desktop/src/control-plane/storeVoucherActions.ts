import type { ControlPlaneCustomerVoucher } from '@store/types';
import { storeControlPlaneClient } from './client';

type LoadCustomerVouchersArgs = {
  accessToken: string;
  tenantId: string;
  customerProfileId: string;
};

export async function runLoadCustomerVouchers({
  accessToken,
  tenantId,
  customerProfileId,
}: LoadCustomerVouchersArgs): Promise<ControlPlaneCustomerVoucher[]> {
  const response = await storeControlPlaneClient.listCustomerVouchers(accessToken, tenantId, customerProfileId);
  return response.records;
}
