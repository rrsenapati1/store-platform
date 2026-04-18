import type {
  ControlPlaneBranchCatalogItem,
  ControlPlaneCheckoutPricePreview,
} from '@store/types';
import { storeControlPlaneClient } from './client';
import { resolveGiftCardCodePayload } from './storeGiftCardActions';
import { resolvePromotionCodePayload } from './storePromotionActions';
import type { StoreSaleComplianceDraft } from './storeSaleComplianceActions';
import { buildSerializedSaleLineInput } from './storeSerializedSaleActions';

type LoadCheckoutPricePreviewArgs = {
  accessToken: string;
  tenantId: string;
  branchId: string;
  cashierSessionId: string;
  selectedCatalogItem: ControlPlaneBranchCatalogItem | null;
  customerProfileId: string | null;
  customerVoucherId: string | null;
  customerName: string;
  customerGstin: string;
  promotionCode: string;
  giftCardCode: string;
  giftCardAmount: number;
  loyaltyPointsToRedeem: number;
  storeCreditAmount: number;
  saleQuantity: string;
  saleSerialNumbers: string;
  saleComplianceDraft: StoreSaleComplianceDraft;
};

export async function runLoadCheckoutPricePreview({
  accessToken,
  tenantId,
  branchId,
  cashierSessionId,
  selectedCatalogItem,
  customerProfileId,
  customerVoucherId,
  customerName,
  customerGstin,
  promotionCode,
  giftCardCode,
  giftCardAmount,
  loyaltyPointsToRedeem,
  storeCreditAmount,
  saleQuantity,
  saleSerialNumbers,
  saleComplianceDraft,
}: LoadCheckoutPricePreviewArgs): Promise<ControlPlaneCheckoutPricePreview> {
  if (!selectedCatalogItem) {
    throw new Error('Select a billable catalog item before refreshing checkout pricing.');
  }
  return storeControlPlaneClient.getCheckoutPricePreview(accessToken, tenantId, branchId, {
    cashier_session_id: cashierSessionId,
    customer_profile_id: customerProfileId,
    customer_name: customerName,
    customer_gstin: customerGstin || null,
    promotion_code: resolvePromotionCodePayload(promotionCode),
    customer_voucher_id: customerVoucherId,
    loyalty_points_to_redeem: loyaltyPointsToRedeem,
    store_credit_amount: storeCreditAmount,
    gift_card_code: resolveGiftCardCodePayload(giftCardCode),
    gift_card_amount: giftCardAmount,
    lines: [buildSerializedSaleLineInput(selectedCatalogItem, saleQuantity, saleSerialNumbers, saleComplianceDraft)],
  });
}
