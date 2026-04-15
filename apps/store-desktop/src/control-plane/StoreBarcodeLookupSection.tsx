import { ActionButton, DetailList, FormField, SectionCard } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

export function StoreBarcodeLookupSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const isPackagedRuntime = workspace.runtimeShellKind === 'packaged_desktop';

  return (
    <SectionCard eyebrow="Barcode lookup" title="Counter scan lookup">
      <FormField id="scanned-barcode" label="Scanned barcode" value={workspace.scannedBarcode} onChange={workspace.setScannedBarcode} />
      <ActionButton
        onClick={() => void workspace.lookupScannedBarcode()}
        disabled={workspace.isBusy || !workspace.isSessionLive || !workspace.scannedBarcode}
      >
        Lookup scanned barcode
      </ActionButton>

      {isPackagedRuntime ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Scanner diagnostics</h3>
          <DetailList
            items={[
              { label: 'Scanner capture', value: workspace.runtimeScannerCaptureState ?? 'Unavailable' },
              { label: 'Scanner transport', value: workspace.runtimeScannerTransport ?? 'Unknown' },
              { label: 'Last scan', value: workspace.runtimeScannerLastScanAt ?? 'No scanner activity yet' },
              { label: 'Last scan preview', value: workspace.runtimeScannerLastScanPreview ?? 'No scanner activity yet' },
              { label: 'Scanner status', value: workspace.runtimeScannerStatusMessage ?? 'No scanner diagnostics available' },
              { label: 'Setup hint', value: workspace.runtimeScannerSetupHint ?? 'No scanner setup guidance available' },
            ]}
          />
        </div>
      ) : null}

      {isPackagedRuntime ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Discovered local scanners</h3>
          {workspace.runtimePreferredScannerId ? (
            <p style={{ marginTop: 0, color: '#4e5871' }}>
              Preferred scanner: <strong>{workspace.runtimePreferredScannerId}</strong>
            </p>
          ) : null}
          <ul style={{ margin: 0, color: '#4e5871', lineHeight: 1.7 }}>
            {workspace.runtimeHardwareScanners.length ? (
              workspace.runtimeHardwareScanners.map((scanner) => (
                <li key={scanner.id} style={{ marginBottom: '12px' }}>
                  <strong>{scanner.label}</strong>
                  <span> :: {scanner.transport} :: {scanner.is_connected ? 'connected' : 'disconnected'}</span>
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '8px' }}>
                    <ActionButton onClick={() => void workspace.assignRuntimePreferredScanner(scanner.id)} disabled={workspace.isBusy}>
                      Use as preferred scanner
                    </ActionButton>
                    {workspace.runtimePreferredScannerId === scanner.id ? (
                      <ActionButton onClick={() => void workspace.assignRuntimePreferredScanner(null)} disabled={workspace.isBusy}>
                        Clear preferred scanner
                      </ActionButton>
                    ) : null}
                  </div>
                </li>
              ))
            ) : (
              <li>No local HID scanner candidates discovered yet.</li>
            )}
          </ul>
        </div>
      ) : null}

      {workspace.latestScanLookup ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Latest scan lookup</h3>
          <DetailList
            items={[
              { label: 'Product', value: workspace.latestScanLookup.product_name },
              { label: 'Barcode', value: workspace.latestScanLookup.barcode },
              { label: 'Selling price', value: String(workspace.latestScanLookup.selling_price) },
              { label: 'Stock on hand', value: String(workspace.latestScanLookup.stock_on_hand) },
            ]}
          />
        </div>
      ) : null}
    </SectionCard>
  );
}
