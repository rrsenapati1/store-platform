/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { describe, expect, test } from 'vitest';
import { StorePrintQueueSection } from './StorePrintQueueSection';

describe('store print queue section barcode jobs', () => {
  test('renders barcode label payloads without assuming invoice fields', () => {
    render(
      <StorePrintQueueSection
        workspace={{
          selectedRuntimeDeviceId: 'device-1',
          setSelectedRuntimeDeviceId: () => undefined,
          runtimeDevices: [
            {
              id: 'device-1',
              tenant_id: 'tenant-acme',
              branch_id: 'branch-1',
              device_name: 'Counter Desktop 1',
              device_code: 'counter-1',
              session_surface: 'store_desktop',
              status: 'ACTIVE',
              assigned_staff_profile_id: null,
              assigned_staff_full_name: null,
            },
          ],
          queueLatestInvoicePrint: async () => undefined,
          queueLatestCreditNotePrint: async () => undefined,
          heartbeatRuntimeDevice: async () => undefined,
          refreshPrintQueue: async () => undefined,
          completeFirstPrintJob: async () => undefined,
          isBusy: false,
          isSessionLive: true,
          latestSale: null,
          latestSaleReturn: null,
          runtimeHeartbeat: null,
          latestPrintJob: {
            id: 'print-job-1',
            tenant_id: 'tenant-acme',
            branch_id: 'branch-1',
            device_id: 'device-1',
            reference_type: 'catalog_product',
            reference_id: 'product-1',
            job_type: 'BARCODE_LABEL',
            copies: 2,
            status: 'QUEUED',
            failure_reason: null,
            payload: {
              labels: [
                {
                  sku_code: 'tea-classic-250g',
                  product_name: 'Classic Tea',
                  barcode: 'ACMETEACLASSIC',
                  price_label: 'Rs. 89.00',
                },
              ],
            },
          },
          printJobs: [
            {
              id: 'print-job-1',
              tenant_id: 'tenant-acme',
              branch_id: 'branch-1',
              device_id: 'device-1',
              reference_type: 'catalog_product',
              reference_id: 'product-1',
              job_type: 'BARCODE_LABEL',
              copies: 2,
              status: 'QUEUED',
              failure_reason: null,
              payload: {
                labels: [
                  {
                    sku_code: 'tea-classic-250g',
                    product_name: 'Classic Tea',
                    barcode: 'ACMETEACLASSIC',
                    price_label: 'Rs. 89.00',
                  },
                ],
              },
            },
          ],
        } as never}
      />,
    );

    expect(screen.getByText('Preview')).toBeInTheDocument();
    expect(screen.getAllByText(/Classic Tea :: Rs. 89.00/)).toHaveLength(2);
  });
});
