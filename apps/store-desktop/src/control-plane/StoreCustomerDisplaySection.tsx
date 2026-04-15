import { ActionButton, DetailList, SectionCard, StatusBadge } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';
import { useCustomerDisplayController } from '../customer-display/useCustomerDisplayController';
import { isNativeStoreCustomerDisplayAvailable } from '../customer-display/nativeStoreCustomerDisplay';

function buildDisplayTone(state: ReturnType<typeof useCustomerDisplayController>['payload']['state']) {
  if (state === 'sale_complete') {
    return 'success';
  }
  if (state === 'payment_in_progress') {
    return 'warning';
  }
  return 'neutral';
}

export function StoreCustomerDisplaySection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const controller = useCustomerDisplayController(workspace);
  const displayBridge = workspace.runtimeShellKind === 'packaged_desktop' && isNativeStoreCustomerDisplayAvailable()
    ? 'Packaged window'
    : 'Browser popup fallback';

  return (
    <SectionCard eyebrow="Customer-facing surface" title="Customer display">
      <DetailList
        items={[
          { label: 'Window', value: controller.isOpen ? 'Open' : 'Closed' },
          { label: 'Bridge', value: displayBridge },
          { label: 'Display state', value: <StatusBadge label={controller.payload.state} tone={buildDisplayTone(controller.payload.state)} /> },
          { label: 'Current total', value: controller.payload.grand_total === null ? '--' : controller.payload.grand_total.toFixed(2) },
        ]}
      />
      <div style={{ display: 'flex', gap: '12px', marginTop: '16px', flexWrap: 'wrap' }}>
        <ActionButton
          onClick={() => void controller.openDisplay()}
          disabled={workspace.isBusy || (!workspace.branchCatalogItems.length && !workspace.latestSale)}
        >
          Open customer display
        </ActionButton>
        <ActionButton
          onClick={() => void controller.closeDisplay()}
          disabled={!controller.isOpen}
        >
          Close customer display
        </ActionButton>
      </div>
      <p style={{ color: '#4e5871', marginBottom: 0 }}>
        The display is read-only and mirrors the active cashier checkout without gaining any billing or control-plane authority.
      </p>
      {controller.errorMessage ? <p style={{ color: '#9d2b19', marginBottom: 0 }}>{controller.errorMessage}</p> : null}
    </SectionCard>
  );
}
