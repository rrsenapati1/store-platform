import { useEffect, useRef, useState } from 'react';
import type {
  ControlPlaneBranchCatalogItem,
  ControlPlaneCheckoutPaymentSession,
  ControlPlaneInventorySnapshotRecord,
  ControlPlaneSale,
  ControlPlaneSaleRecord,
} from '@store/types';
import { storeControlPlaneClient } from './client';

const CASHFREE_POLL_INTERVAL_MS = 2500;

interface UseStoreRuntimeCheckoutPaymentArgs {
  accessToken: string;
  tenantId: string;
  branchId: string;
  selectedCatalogItem: ControlPlaneBranchCatalogItem | null;
  customerName: string;
  customerGstin: string;
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

function isTerminalStatus(lifecycleStatus: string) {
  return lifecycleStatus === 'FINALIZED'
    || lifecycleStatus === 'FAILED'
    || lifecycleStatus === 'EXPIRED'
    || lifecycleStatus === 'CANCELED';
}

export function useStoreRuntimeCheckoutPayment({
  accessToken,
  tenantId,
  branchId,
  selectedCatalogItem,
  customerName,
  customerGstin,
  saleQuantity,
  paymentMethod,
  isSessionLive,
  onError,
  onFinalized,
}: UseStoreRuntimeCheckoutPaymentArgs) {
  const [checkoutPaymentSession, setCheckoutPaymentSession] = useState<ControlPlaneCheckoutPaymentSession | null>(null);
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

  async function startCheckoutPaymentSession() {
    if (!selectedCatalogItem) {
      onError('Select a billable catalog item before starting a QR payment.');
      return;
    }
    if (!isSessionLive || !accessToken || !tenantId || !branchId) {
      onError('Cashfree UPI QR requires a live online runtime session. Use a manual payment method for offline continuity.');
      return;
    }
    const quantity = Number(saleQuantity);
    if (!Number.isFinite(quantity) || quantity <= 0) {
      onError('Sale quantity must be a positive number.');
      return;
    }
    setIsBusy(true);
    try {
      finalizedSessionRef.current = null;
      const session = await storeControlPlaneClient.createCheckoutPaymentSession(accessToken, tenantId, branchId, {
        provider_name: 'cashfree',
        payment_method: paymentMethod,
        customer_name: customerName,
        customer_gstin: customerGstin || null,
        lines: [{ product_id: selectedCatalogItem.product_id, quantity }],
      });
      setCheckoutPaymentSession(session);
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unable to start Cashfree UPI QR payment.');
    } finally {
      setIsBusy(false);
    }
  }

  async function retryCheckoutPaymentSession() {
    await startCheckoutPaymentSession();
  }

  async function cancelCheckoutPaymentSession() {
    if (!checkoutPaymentSession || !accessToken || !tenantId || !branchId) {
      setCheckoutPaymentSession(null);
      return;
    }
    if (checkoutPaymentSession.lifecycle_status === 'FINALIZED') {
      return;
    }
    setIsBusy(true);
    try {
      const canceledSession = await storeControlPlaneClient.cancelCheckoutPaymentSession(
        accessToken,
        tenantId,
        branchId,
        checkoutPaymentSession.id,
      );
      setCheckoutPaymentSession(canceledSession);
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unable to cancel Cashfree UPI QR payment.');
    } finally {
      setIsBusy(false);
    }
  }

  function clearCheckoutPaymentSession() {
    finalizedSessionRef.current = null;
    setCheckoutPaymentSession(null);
  }

  useEffect(() => {
    if (!checkoutPaymentSession || !accessToken || !tenantId || !branchId || isTerminalStatus(checkoutPaymentSession.lifecycle_status)) {
      if (checkoutPaymentSession?.lifecycle_status === 'FINALIZED' && checkoutPaymentSession.sale) {
        void refreshFinalizedSale(checkoutPaymentSession, accessToken, tenantId, branchId).catch((error) => {
          onErrorRef.current(error instanceof Error ? error.message : 'Unable to refresh finalized Cashfree payment sale.');
        });
      }
      return;
    }

    const timeoutId = globalThis.setTimeout(() => {
      void (async () => {
        try {
          const nextSession = await storeControlPlaneClient.getCheckoutPaymentSession(
            accessToken,
            tenantId,
            branchId,
            checkoutPaymentSession.id,
          );
          setCheckoutPaymentSession(nextSession);
          if (nextSession.lifecycle_status === 'FINALIZED' && nextSession.sale) {
            await refreshFinalizedSale(nextSession, accessToken, tenantId, branchId);
          }
        } catch (error) {
          onErrorRef.current(error instanceof Error ? error.message : 'Unable to refresh Cashfree UPI QR payment status.');
        }
      })();
    }, CASHFREE_POLL_INTERVAL_MS);

    return () => {
      globalThis.clearTimeout(timeoutId);
    };
  }, [accessToken, branchId, checkoutPaymentSession, tenantId]);

  return {
    checkoutPaymentSession,
    clearCheckoutPaymentSession,
    cancelCheckoutPaymentSession,
    isBusy,
    retryCheckoutPaymentSession,
    startCheckoutPaymentSession,
  };
}
