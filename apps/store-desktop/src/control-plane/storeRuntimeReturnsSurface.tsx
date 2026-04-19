import type { CSSProperties } from 'react';
import { SectionCard } from '@store/ui';
import { StoreExchangeSection } from './StoreExchangeSection';
import { StoreOfflineContinuitySection } from './StoreOfflineContinuitySection';
import { StoreReturnsSection } from './StoreReturnsSection';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

const surfaceGridStyle: CSSProperties = {
  display: 'grid',
  gap: '16px',
  gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
  alignItems: 'start',
};

export function StoreRuntimeReturnsSurface({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  return (
    <div style={{ display: 'grid', gap: '16px' }}>
      <SectionCard eyebrow="Counter returns" title="Returns and exchanges">
        <p style={{ margin: 0, color: '#4e5871' }}>
          Group post-sale corrections, reversals, and continuity checks into one lighter counter surface.
        </p>
      </SectionCard>

      <div style={surfaceGridStyle}>
        <StoreReturnsSection workspace={workspace} />
        <StoreExchangeSection workspace={workspace} />
        <div style={{ gridColumn: '1 / -1' }}>
          <StoreOfflineContinuitySection workspace={workspace} />
        </div>
      </div>
    </div>
  );
}
