import type { CSSProperties } from 'react';
import { SectionCard } from '@store/ui';
import { StoreBarcodeLookupSection } from './StoreBarcodeLookupSection';
import { StoreBatchExpirySection } from './StoreBatchExpirySection';
import { StorePrintQueueSection } from './StorePrintQueueSection';
import { StoreReceivingSection } from './StoreReceivingSection';
import { StoreRestockSection } from './StoreRestockSection';
import { StoreRuntimeShellSection } from './StoreRuntimeShellSection';
import { StoreStockCountSection } from './StoreStockCountSection';
import { StoreRuntimeOutboxSection } from './StoreRuntimeOutboxSection';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

const surfaceGridStyle: CSSProperties = {
  display: 'grid',
  gap: '16px',
  gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
  alignItems: 'start',
};

export function StoreRuntimeOperationsSurface({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  return (
    <div style={{ display: 'grid', gap: '16px' }}>
      <SectionCard eyebrow="Stock operations" title="Operations desk">
        <p style={{ margin: 0, color: '#4e5871' }}>
          Keep scan lookup, receiving, restock, count, expiry, and print controls in one compact operations surface.
        </p>
      </SectionCard>

      <div style={surfaceGridStyle}>
        <StoreBarcodeLookupSection workspace={workspace} />
        <StoreReceivingSection workspace={workspace} />
        <StoreRestockSection workspace={workspace} />
        <StoreStockCountSection workspace={workspace} />
        <StoreBatchExpirySection workspace={workspace} />
        <div style={{ gridColumn: '1 / -1' }}>
          <StoreRuntimeShellSection workspace={workspace} />
        </div>
        <div style={{ gridColumn: '1 / -1' }}>
          <StorePrintQueueSection workspace={workspace} />
        </div>
        <div style={{ gridColumn: '1 / -1' }}>
          <StoreRuntimeOutboxSection workspace={workspace} />
        </div>
      </div>
    </div>
  );
}
