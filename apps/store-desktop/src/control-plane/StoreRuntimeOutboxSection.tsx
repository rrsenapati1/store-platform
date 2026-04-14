import { ActionButton, SectionCard } from '@store/ui';
import { describePendingRuntimeMutation } from './runtimeOutbox';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

export function StoreRuntimeOutboxSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  return (
    <SectionCard eyebrow="Runtime continuity" title={`Queued runtime actions: ${workspace.pendingMutationCount}`}>
      <p style={{ marginTop: 0, color: '#4e5871' }}>
        Only replayable runtime actions are queued locally here. This improves branch continuity without turning the desktop shell into the system of record.
      </p>

      <ActionButton
        onClick={() => void workspace.replayPendingRuntimeActions()}
        disabled={workspace.isBusy || !workspace.isSessionLive || workspace.pendingMutationCount === 0}
      >
        Replay pending runtime actions
      </ActionButton>

      <ul style={{ marginTop: '16px', marginBottom: 0, color: '#4e5871', lineHeight: 1.7 }}>
        {workspace.pendingRuntimeMutations.length ? (
          workspace.pendingRuntimeMutations.map((mutation) => (
            <li key={mutation.id}>
              {describePendingRuntimeMutation(mutation)} :: {mutation.created_at}
            </li>
          ))
        ) : (
          <li>No runtime actions are currently queued for replay.</li>
        )}
      </ul>
    </SectionCard>
  );
}
