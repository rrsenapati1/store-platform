import type {
  ControlPlaneBranchCatalogItem,
  ControlPlaneCheckoutPricePreview,
} from '@store/types';
import { storeControlPlaneClient } from './client';
import { resolvePromotionCodePayload } from './storePromotionActions';

type LoadCheckoutPricePreviewArgs = {
  accessToken: string;
  tenantId: string;
  branchId: string;
  selectedCatalogItem: ControlPlaneBranchCatalogItem | null;
  customerProfileId: string | null;
  customerName: string;
  customerGstin: string;
  promotionCode: string;
  loyaltyPointsToRedeem: number;
  storeCreditAmount: number;
  saleQuantity: string;
};

export async function runLoadCheckoutPricePreview({
  accessToken,
  tenantId,
  branchId,
  selectedCatalogItem,
  customerProfileId,
  customerName,
  customerGstin,
  promotionCode,
  loyaltyPointsToRedeem,
  storeCreditAmount,
  saleQuantity,
}: LoadCheckoutPricePreviewArgs): Promise<ControlPlaneCheckoutPricePreview> {
  if (!selectedCatalogItem) {
    throw new Error('Select a billable catalog item before refreshing checkout pricing.');
  }
  const quantity = Number(saleQuantity);
  if (!Number.isFinite(quantity) || quantity <= 0) {
    throw new Error('Sale quantity must be a positive number.');
  }
  return storeControlPlaneClient.getCheckoutPricePreview(accessToken, tenantId, branchId, {
    customer_profile_id: customerProfileId,
    customer_name: customerName,
    customer_gstin: customerGstin || null,
    promotion_code: resolvePromotionCodePayload(promotionCode),
    loyalty_points_to_redeem: loyaltyPointsToRedeem,
    store_credit_amount: storeCreditAmount,
    lines: [{ product_id: selectedCatalogItem.product_id, quantity }],
  });
}
