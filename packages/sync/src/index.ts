import type { MutationConflictInput, MutationConflictResult, PullResponse, SyncRecord } from '@store/types';

export function resolveMutationConflict(input: MutationConflictInput): MutationConflictResult {
  if (input.clientVersion < input.serverVersion) {
    return {
      accepted: false,
      conflict: true,
      nextVersion: input.serverVersion,
    };
  }

  return {
    accepted: true,
    conflict: false,
    nextVersion: input.serverVersion + 1,
  };
}

export function buildPullResponse(input: { records: SyncRecord[] }): PullResponse {
  const records = [...input.records].sort((left, right) => left.version - right.version);
  return {
    cursor: records.at(-1)?.version ?? 0,
    records,
  };
}

export function heartbeatStatus(input: { secondsSinceSync: number }): 'current' | 'reconnecting' | 'stale' {
  if (input.secondsSinceSync <= 15) {
    return 'current';
  }
  if (input.secondsSinceSync <= 90) {
    return 'reconnecting';
  }
  return 'stale';
}
