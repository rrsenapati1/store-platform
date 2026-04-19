import { useEffect, useRef, useState } from 'react';
import type { StoreRuntimeWorkspaceState } from '../control-plane/useStoreRuntimeWorkspace';
import {
  buildCustomerDisplayPayload,
  clearCustomerDisplayPayload,
  saveCustomerDisplayPayload,
} from './customerDisplayModel';
import { createNativeStoreCustomerDisplay } from './nativeStoreCustomerDisplay';

export function useCustomerDisplayController(workspace: StoreRuntimeWorkspaceState) {
  const adapterRef = useRef(createNativeStoreCustomerDisplay());
  const [isOpen, setIsOpen] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const selectedItem = workspace.branchCatalogItems[0]
    ? {
        product_name: workspace.branchCatalogItems[0].product_name,
        effective_selling_price: workspace.branchCatalogItems[0].effective_selling_price,
        gst_rate: workspace.branchCatalogItems[0].gst_rate,
      }
    : null;
  const latestSale = workspace.latestSale
    ? {
        customer_name: workspace.latestSale.customer_name,
        invoice_number: workspace.latestSale.invoice_number,
        issued_on: workspace.latestSale.issued_on,
        subtotal: workspace.latestSale.subtotal,
        cgst_total: workspace.latestSale.cgst_total,
        sgst_total: workspace.latestSale.sgst_total,
        igst_total: workspace.latestSale.igst_total,
        grand_total: workspace.latestSale.grand_total,
        payment: workspace.latestSale.payment,
        lines: (workspace.latestSale.lines ?? []).map((line) => ({
          product_name: line.product_name,
          quantity: line.quantity,
          line_total: line.line_total,
        })),
      }
    : null;
  const payload = buildCustomerDisplayPayload({
    branchName: workspace.branches?.[0]?.name ?? workspace.branchId ?? null,
    selectedItem,
    saleQuantity: workspace.saleQuantity,
    paymentMethod: workspace.paymentMethod,
    latestSale,
    checkoutPaymentSession: workspace.checkoutPaymentSession
      ? {
          payment_method: workspace.checkoutPaymentSession.payment_method,
          handoff_surface: workspace.checkoutPaymentSession.handoff_surface,
          lifecycle_status: workspace.checkoutPaymentSession.lifecycle_status,
          order_amount: workspace.checkoutPaymentSession.order_amount,
          currency_code: workspace.checkoutPaymentSession.currency_code,
          action_payload: {
            kind: workspace.checkoutPaymentSession.action_payload.kind,
            value: workspace.checkoutPaymentSession.action_payload.value,
            label: workspace.checkoutPaymentSession.action_payload.label ?? null,
            description: workspace.checkoutPaymentSession.action_payload.description ?? null,
            handoff_surface: workspace.checkoutPaymentSession.handoff_surface,
          },
          action_expires_at: workspace.checkoutPaymentSession.action_expires_at ?? null,
          qr_payload: workspace.checkoutPaymentSession.qr_payload
            ? {
                format: workspace.checkoutPaymentSession.qr_payload.format,
                value: workspace.checkoutPaymentSession.qr_payload.value,
              }
            : null,
          qr_expires_at: workspace.checkoutPaymentSession.qr_expires_at ?? null,
        }
      : null,
    isBusy: workspace.isBusy,
  });
  const payloadSignature = JSON.stringify(payload);

  useEffect(() => {
    if (!isOpen) {
      return;
    }
    saveCustomerDisplayPayload(payload);
  }, [isOpen, payload, payloadSignature]);

  async function openDisplay() {
    setErrorMessage('');
    try {
      setIsOpen(true);
      saveCustomerDisplayPayload(payload);
      await adapterRef.current.open();
    } catch (error) {
      setIsOpen(false);
      setErrorMessage(error instanceof Error ? error.message : 'Unable to open the customer display.');
    }
  }

  async function closeDisplay() {
    setErrorMessage('');
    try {
      await adapterRef.current.close();
      clearCustomerDisplayPayload();
      setIsOpen(false);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to close the customer display.');
    }
  }

  return {
    errorMessage,
    isOpen,
    openDisplay,
    closeDisplay,
    payload,
  };
}
