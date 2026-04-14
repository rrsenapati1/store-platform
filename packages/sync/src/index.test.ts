import { describe, expect, test } from 'vitest';
import { buildPullResponse, heartbeatStatus, resolveMutationConflict } from './index';

describe('offline sync posture', () => {
  test('rejects stale mutations when the client version lags the server', () => {
    expect(resolveMutationConflict({ clientVersion: 2, serverVersion: 4 })).toEqual({
      accepted: false,
      conflict: true,
      nextVersion: 4,
    });
  });

  test('accepts current mutations and increments the version', () => {
    expect(resolveMutationConflict({ clientVersion: 4, serverVersion: 4 })).toEqual({
      accepted: true,
      conflict: false,
      nextVersion: 5,
    });
  });

  test('builds a pull response with ordered records and cursor state', () => {
    expect(
      buildPullResponse({
        records: [
          { id: 'a', version: 1 },
          { id: 'b', version: 3 },
        ],
      }),
    ).toEqual({
      cursor: 3,
      records: [
        { id: 'a', version: 1 },
        { id: 'b', version: 3 },
      ],
    });
  });

  test('reports heartbeat freshness windows', () => {
    expect(heartbeatStatus({ secondsSinceSync: 5 })).toBe('current');
    expect(heartbeatStatus({ secondsSinceSync: 55 })).toBe('reconnecting');
    expect(heartbeatStatus({ secondsSinceSync: 180 })).toBe('stale');
  });
});
