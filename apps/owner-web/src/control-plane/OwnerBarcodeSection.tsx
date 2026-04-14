import { ActionButton, DetailList, FormField, SectionCard } from '@store/ui';
import type { OwnerWorkspaceState } from './useOwnerWorkspace';

export function OwnerBarcodeSection({ workspace }: { workspace: OwnerWorkspaceState }) {
  const firstProduct = workspace.catalogProducts[0] ?? null;

  return (
    <SectionCard eyebrow="Barcode foundation" title="Catalog barcode operations">
      <FormField
        id="barcode-manual-value"
        label="Manual barcode override"
        value={workspace.barcodeManualValue}
        onChange={workspace.setBarcodeManualValue}
        placeholder="Leave blank to auto-allocate from tenant and SKU"
      />
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <ActionButton
          onClick={() => void workspace.allocateFirstProductBarcode()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.branchId || !firstProduct}
        >
          Allocate first product barcode
        </ActionButton>
        <ActionButton
          onClick={() => void workspace.previewFirstProductBarcodeLabel()}
          disabled={workspace.isBusy || !workspace.actor || !workspace.branchId || !firstProduct}
        >
          Preview first product label
        </ActionButton>
      </div>

      {workspace.latestBarcodeAllocation ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Latest barcode allocation</h3>
          <DetailList
            items={[
              { label: 'Barcode', value: workspace.latestBarcodeAllocation.barcode },
              { label: 'Source', value: workspace.latestBarcodeAllocation.source },
            ]}
          />
        </div>
      ) : null}

      {workspace.latestBarcodeLabelPreview ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Latest barcode label preview</h3>
          <DetailList
            items={[
              { label: 'Product', value: workspace.latestBarcodeLabelPreview.product_name },
              { label: 'Barcode', value: workspace.latestBarcodeLabelPreview.barcode },
              { label: 'Price label', value: workspace.latestBarcodeLabelPreview.price_label },
            ]}
          />
        </div>
      ) : null}
    </SectionCard>
  );
}
