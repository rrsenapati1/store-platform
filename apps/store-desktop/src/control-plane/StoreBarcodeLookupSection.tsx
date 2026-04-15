import { ActionButton, DetailList, FormField, SectionCard } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

export function StoreBarcodeLookupSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const isPackagedRuntime = workspace.runtimeShellKind === 'packaged_desktop';
  const runtimeHardwareScales = workspace.runtimeHardwareScales ?? [];
  const preferredScaleLabel = runtimeHardwareScales.find(
    (scale) => scale.id === workspace.runtimePreferredScaleId,
  )?.label ?? workspace.runtimePreferredScaleId;

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
          <h3 style={{ marginBottom: '10px' }}>Scale diagnostics</h3>
          <DetailList
            items={[
              { label: 'Scale capture', value: workspace.runtimeScaleCaptureState ?? 'Unavailable' },
              {
                label: 'Last weight',
                value: workspace.runtimeScaleLastWeightValue !== null && workspace.runtimeScaleLastWeightUnit
                  ? `${workspace.runtimeScaleLastWeightValue} ${workspace.runtimeScaleLastWeightUnit}`
                  : 'No live weight captured yet',
              },
              { label: 'Last weight read', value: workspace.runtimeScaleLastWeightReadAt ?? 'No live weight captured yet' },
              { label: 'Scale status', value: workspace.runtimeScaleStatusMessage ?? 'No scale diagnostics available' },
              { label: 'Setup hint', value: workspace.runtimeScaleSetupHint ?? 'No scale setup guidance available' },
            ]}
          />
          <div style={{ marginTop: '10px' }}>
            <ActionButton
              onClick={() => void workspace.readRuntimeScaleWeight()}
              disabled={workspace.isBusy || !workspace.isSessionLive || !workspace.runtimePreferredScaleId}
            >
              Read current weight
            </ActionButton>
          </div>
        </div>
      ) : null}

      {isPackagedRuntime ? (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ marginBottom: '10px' }}>Discovered local scales</h3>
          {workspace.runtimePreferredScaleId ? (
            <p style={{ marginTop: 0, color: '#4e5871' }}>
              Preferred scale: <strong>{preferredScaleLabel}</strong>
            </p>
          ) : null}
          <ul style={{ margin: 0, color: '#4e5871', lineHeight: 1.7 }}>
            {runtimeHardwareScales.length ? (
              runtimeHardwareScales.map((scale) => (
                <li key={scale.id} style={{ marginBottom: '12px' }}>
                  <strong>{scale.label}</strong>
                  <span> :: {scale.transport} :: {scale.is_connected ? 'connected' : 'disconnected'}</span>
                  <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '8px' }}>
                    <ActionButton onClick={() => void workspace.assignRuntimePreferredScale(scale.id)} disabled={workspace.isBusy}>
                      Use as preferred scale
                    </ActionButton>
                    {workspace.runtimePreferredScaleId === scale.id ? (
                      <ActionButton onClick={() => void workspace.assignRuntimePreferredScale(null)} disabled={workspace.isBusy}>
                        Clear preferred scale
                      </ActionButton>
                    ) : null}
                  </div>
                </li>
              ))
            ) : (
              <li>No local serial scale candidates discovered yet.</li>
            )}
          </ul>
        </div>
      ) : null}

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
