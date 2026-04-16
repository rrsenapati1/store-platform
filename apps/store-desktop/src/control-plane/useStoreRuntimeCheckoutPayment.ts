import { useEffect, useRef, useState } from 'react';
import type {
  ControlPlaneBranchCatalogItem,
  ControlPlaneCheckoutPaymentSession,
  ControlPlaneInventorySnapshotRecord,
  ControlPlaneSale,
  ControlPlaneSaleRecord,
} from '@store/types';
import { storeControlPlaneClient } from './client';
import { resolvePromotionCodePayload } from './storePromotionActions';

const CASHFREE_POLL_INTERVAL_MS = 2500;

interface UseStoreRuntimeCheckoutPaymentArgs {
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
  paymentMethod: string;
  isSessionLive: boolean;
  onError(message: string): void;
  onFinalized(args: {
    sale: ControlPlaneSale;
    sales: ControlPlaneSaleRecord[];
    inventorySnapshot: ControlPlaneInventorySnapshotRecord[];
  }): void;
}

interface CheckoutMethodConfiguration {
  handoffSurface: string;
  providerPaymentMode: string;
}

function isProviderBackedCheckoutMethod(paymentMethod: string) {
  return paymentMethod === 'CASHFREE_UPI_QR'
    || paymentMethod === 'CASHFREE_HOSTED_TERMINAL'
    || paymentMethod === 'CASHFREE_HOSTED_PHONE';
}

function isTerminalStatus(lifecycleStatus: string) {
  return lifecycleStatus === 'FINALIZED'
    || lifecycleStatus === 'FAILED'
    || lifecycleStatus === 'EXPIRED'
    || lifecycleStatus === 'CANCELED';
}

function resolveCheckoutMethodConfiguration(paymentMethod: string): CheckoutMethodConfiguration {
  if (paymentMethod === 'CASHFREE_UPI_QR') {
    return {
      handoffSurface: 'BRANDED_UPI_QR',
      providerPaymentMode: 'cashfree_upi',
    };
  }
  if (paymentMethod === 'CASHFREE_HOSTED_TERMINAL') {
    return {
      handoffSurface: 'HOSTED_TERMINAL',
      providerPaymentMode: 'cashfree_checkout',
    };
  }
  if (paymentMethod === 'CASHFREE_HOSTED_PHONE') {
    return {
      handoffSurface: 'HOSTED_PHONE',
      providerPaymentMode: 'cashfree_checkout',
    };
  }
  throw new Error(`Unsupported checkout payment method: ${paymentMethod}`);
}

export function useStoreRuntimeCheckoutPayment({
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
  paymentMethod,
  isSessionLive,
  onError,
  onFinalized,
}: UseStoreRuntimeCheckoutPaymentArgs) {
  const [checkoutPaymentSession, setCheckoutPaymentSession] = useState<ControlPlaneCheckoutPaymentSession | null>(null);
  const [checkoutPaymentHistory, setCheckoutPaymentHistory] = useState<ControlPlaneCheckoutPaymentSession[]>([]);
  const [isBusy, setIsBusy] = useState(false);
  const finalizedSessionRef = useRef<string | null>(null);
  const onErrorRef = useRef(onError);
  const onFinalizedRef = useRef(onFinalized);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    onFinalizedRef.current = onFinalized;
  }, [onFinalized]);

  async function refreshFinalizedSale(
    session: ControlPlaneCheckoutPaymentSession,
    activeAccessToken: string = accessToken,
    activeTenantId: string = tenantId,
    activeBranchId: string = branchId,
  ) {
    if (!session.sale || finalizedSessionRef.current === session.id) {
      return;
    }
    const [salesResponse, snapshotResponse] = await Promise.all([
      storeControlPlaneClient.listSales(activeAccessToken, activeTenantId, activeBranchId),
      storeControlPlaneClient.listInventorySnapshot(activeAccessToken, activeTenantId, activeBranchId),
    ]);
    finalizedSessionRef.current = session.id;
    onFinalizedRef.current({
      sale: session.sale,
      sales: salesResponse.records,
      inventorySnapshot: snapshotResponse.records,
    });
  }

  async function listCheckoutPaymentHistory(
    activeAccessToken: string = accessToken,
    activeTenantId: string = tenantId,
    activeBranchId: string = branchId,
  ) {
    if (!activeAccessToken || !activeTenantId || !activeBranchId) {
      setCheckoutPaymentHistory([]);
      return [];
    }
    const response = await storeControlPlaneClient.listCheckoutPaymentSessions(
      activeAccessToken,
      activeTenantId,
      activeBranchId,
    );
    setCheckoutPaymentHistory(response.records);
    return response.records;
  }

  async function startCheckoutPaymentSession() {
    if (!selectedCatalogItem) {
      onError('Select a billable catalog item before starting digital checkout.');
      return;
    }
    if (!isSessionLive || !accessToken || !tenantId || !branchId) {
      onError('Cashfree checkout requires a live online runtime session. Use a manual payment method for offline continuity.');
      return;
    }
    if (!isProviderBackedCheckoutMethod(paymentMethod)) {
      onError('Selected payment method is not backed by Cashfree checkout.');
      return;
    }
    const quantity = Number(saleQuantity);
    if (!Number.isFinite(quantity) || quantity <= 0) {
      onError('Sale quantity must be a positive number.');
      return;
    }
    const methodConfiguration = resolveCheckoutMethodConfiguration(paymentMethod);
    setIsBusy(true);
    try {
      finalizedSessionRef.current = null;
      const session = await storeControlPlaneClient.createCheckoutPaymentSession(accessToken, tenantId, branchId, {
        provider_name: 'cashfree',
        payment_method: paymentMethod,
        handoff_surface: methodConfiguration.handoffSurface,
        provider_payment_mode: methodConfiguration.providerPaymentMode,
        customer_profile_id: customerProfileId,
        customer_name: customerName,
        customer_gstin: customerGstin || null,
        promotion_code: resolvePromotionCodePayload(promotionCode),
        loyalty_points_to_redeem: loyaltyPointsToRedeem,
        store_credit_amount: storeCreditAmount,
        lines: [{ product_id: selectedCatalogItem.product_id, quantity }],
      });
      setCheckoutPaymentSession(session);
      await listCheckoutPaymentHistory();
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unable to start Cashfree checkout.');
    } finally {
      setIsBusy(false);
    }
  }

  async function refreshCheckoutPaymentSession(
    checkoutPaymentSessionId?: string,
    options?: { silent?: boolean },
  ) {
    const targetSessionId = checkoutPaymentSessionId ?? checkoutPaymentSession?.id;
    if (!targetSessionId || !accessToken || !tenantId || !branchId) {
      return null;
    }
    try {
      const nextSession = await storeControlPlaneClient.refreshCheckoutPaymentSession(
        accessToken,
        tenantId,
        branchId,
        targetSessionId,
      );
      setCheckoutPaymentSession((current) => (
        current?.id === nextSession.id || current === null ? nextSession : current
      ));
      await listCheckoutPaymentHistory();
      if (nextSession.lifecycle_status === 'FINALIZED' && nextSession.sale) {
        await refreshFinalizedSale(nextSession, accessToken, tenantId, branchId);
      }
      return nextSession;
    } catch (error) {
      if (!options?.silent) {
        onError(error instanceof Error ? error.message : 'Unable to refresh checkout payment status.');
      }
      return null;
    }
  }

  async function retryCheckoutPaymentSession(checkoutPaymentSessionId?: string) {
    const targetSessionId = checkoutPaymentSessionId ?? checkoutPaymentSession?.id;
    if (!targetSessionId || !accessToken || !tenantId || !branchId) {
      return;
    }
    setIsBusy(true);
    try {
      finalizedSessionRef.current = null;
      const nextSession = await storeControlPlaneClient.retryCheckoutPaymentSession(
        accessToken,
        tenantId,
        branchId,
        targetSessionId,
      );
      setCheckoutPaymentSession(nextSession);
      await listCheckoutPaymentHistory();
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unable to retry checkout payment.');
    } finally {
      setIsBusy(false);
    }
  }

  async function finalizeCheckoutPaymentSession(checkoutPaymentSessionId?: string) {
    const targetSessionId = checkoutPaymentSessionId ?? checkoutPaymentSession?.id;
    if (!targetSessionId || !accessToken || !tenantId || !branchId) {
      return;
    }
    setIsBusy(true);
    try {
      const nextSession = await storeControlPlaneClient.finalizeCheckoutPaymentSession(
        accessToken,
        tenantId,
        branchId,
        targetSessionId,
      );
      setCheckoutPaymentSession(nextSession);
      await listCheckoutPaymentHistory();
      if (nextSession.lifecycle_status === 'FINALIZED' && nextSession.sale) {
        await refreshFinalizedSale(nextSession, accessToken, tenantId, branchId);
      }
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unable to finalize confirmed checkout payment.');
    } finally {
      setIsBusy(false);
    }
  }

  async function cancelCheckoutPaymentSession(checkoutPaymentSessionId?: string) {
    const targetSessionId = checkoutPaymentSessionId ?? checkoutPaymentSession?.id;
    if (!targetSessionId || !accessToken || !tenantId || !branchId) {
      setCheckoutPaymentSession(null);
      return;
    }
    const isCurrentSession = checkoutPaymentSession?.id === targetSessionId;
    if (checkoutPaymentSession?.lifecycle_status === 'FINALIZED' && isCurrentSession) {
      return;
    }
    setIsBusy(true);
    try {
      const canceledSession = await storeControlPlaneClient.cancelCheckoutPaymentSession(
        accessToken,
        tenantId,
        branchId,
        targetSessionId,
      );
      setCheckoutPaymentSession((current) => (current?.id === canceledSession.id || isCurrentSession ? canceledSession : current));
      await listCheckoutPaymentHistory();
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unable to cancel checkout payment.');
    } finally {
      setIsBusy(false);
    }
  }

  function clearCheckoutPaymentSession() {
    finalizedSessionRef.current = null;
    setCheckoutPaymentSession(null);
  }

  useEffect(() => {
    void listCheckoutPaymentHistory().catch((error) => {
      onErrorRef.current(error instanceof Error ? error.message : 'Unable to load recent checkout payments.');
    });
  }, [accessToken, branchId, tenantId]);

  useEffect(() => {
    if (!checkoutPaymentSession || !accessToken || !tenantId || !branchId || isTerminalStatus(checkoutPaymentSession.lifecycle_status)) {
      if (checkoutPaymentSession?.lifecycle_status === 'FINALIZED' && checkoutPaymentSession.sale) {
        void refreshFinalizedSale(checkoutPaymentSession, accessToken, tenantId, branchId).catch((error) => {
          onErrorRef.current(error instanceof Error ? error.message : 'Unable to refresh finalized checkout payment sale.');
        });
      }
      return;
    }

    const timeoutId = globalThis.setTimeout(() => {
      void refreshCheckoutPaymentSession(checkoutPaymentSession.id, { silent: true });
    }, CASHFREE_POLL_INTERVAL_MS);

    return () => {
      globalThis.clearTimeout(timeoutId);
    };
  }, [accessToken, branchId, checkoutPaymentSession, tenantId]);

  return {
    checkoutPaymentSession,
    checkoutPaymentHistory,
    clearCheckoutPaymentSession,
    cancelCheckoutPaymentSession,
    finalizeCheckoutPaymentSession,
    isBusy,
    listCheckoutPaymentHistory,
    refreshCheckoutPaymentSession,
    retryCheckoutPaymentSession,
    startCheckoutPaymentSession,
  };
}
