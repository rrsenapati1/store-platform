import { StoreCustomerDisplaySection } from './StoreCustomerDisplaySection';
import { StoreRuntimeSellCartPanel } from './storeRuntimeSellCartPanel';
import { StoreRuntimeSellPaymentPanel } from './storeRuntimeSellPaymentPanel';
import { StoreRuntimeSellSummaryPanel } from './storeRuntimeSellSummaryPanel';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

export function StoreRuntimeSellSurface({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  return (
    <div
      style={{
        display: 'grid',
        gap: '24px',
        gridTemplateColumns: 'minmax(0, 1.8fr) minmax(320px, 1fr)',
      }}
    >
      <StoreRuntimeSellCartPanel workspace={workspace} />
      <div style={{ display: 'grid', gap: '20px', alignContent: 'start' }}>
        <StoreRuntimeSellSummaryPanel workspace={workspace} />
        <StoreCustomerDisplaySection workspace={workspace} />
        <StoreRuntimeSellPaymentPanel workspace={workspace} />
      </div>
    </div>
  );
}
