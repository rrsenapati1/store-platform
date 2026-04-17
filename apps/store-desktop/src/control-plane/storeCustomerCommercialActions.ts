import type {
  ControlPlaneCustomerLoyalty,
  ControlPlaneCustomerStoreCredit,
  ControlPlaneCustomerVoucher,
  ControlPlaneLoyaltyProgram,
} from '@store/types';
import { runLoadCustomerStoreCredit } from './storeCreditActions';
import { runLoadCustomerLoyalty, runLoadLoyaltyProgram } from './storeLoyaltyActions';
import { runLoadCustomerVouchers } from './storeVoucherActions';

type LoadSelectedCustomerCommercialStateArgs = {
  accessToken: string;
  tenantId: string;
  customerProfileId: string;
};

type SelectedCustomerCommercialState = {
  vouchers: ControlPlaneCustomerVoucher[];
  storeCredit: ControlPlaneCustomerStoreCredit;
  loyaltyProgram: ControlPlaneLoyaltyProgram;
  customerLoyalty: ControlPlaneCustomerLoyalty;
};

export async function runLoadSelectedCustomerCommercialState({
  accessToken,
  tenantId,
  customerProfileId,
}: LoadSelectedCustomerCommercialStateArgs): Promise<SelectedCustomerCommercialState> {
  const [vouchers, storeCredit, loyaltyProgram, customerLoyalty] = await Promise.all([
    runLoadCustomerVouchers({
      accessToken,
      tenantId,
      customerProfileId,
    }),
    runLoadCustomerStoreCredit({
      accessToken,
      tenantId,
      customerProfileId,
    }),
    runLoadLoyaltyProgram({
      accessToken,
      tenantId,
    }),
    runLoadCustomerLoyalty({
      accessToken,
      tenantId,
      customerProfileId,
    }),
  ]);

  return {
    vouchers,
    storeCredit,
    loyaltyProgram,
    customerLoyalty,
  };
}
