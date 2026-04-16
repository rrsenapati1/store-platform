# Store Desktop Reviewed Stock Count Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a board-driven reviewed stock-count workflow to `apps/store-desktop` so desktop operators can create, record, approve, and cancel blind stock-count sessions through the existing control-plane lifecycle.

**Architecture:** Keep the control plane as the only authority and add one dedicated desktop section for reviewed stock counts. Extend the desktop client with reviewed count routes, extract stock-count side effects into a focused `storeStockCountActions.ts` helper instead of growing `useStoreRuntimeWorkspace.ts`, then mount a new `StoreStockCountSection` that mirrors the reviewed lifecycle already used by owner-web and mobile.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, existing `@store/ui` primitives, control-plane REST client helpers in `apps/store-desktop`.

---

## File Structure

- Create: `apps/store-desktop/src/control-plane/client.stock-count.test.ts`
  - Desktop client route coverage for stock-count board and reviewed-session calls.
- Create: `apps/store-desktop/src/control-plane/storeStockCountActions.ts`
  - Focused async helpers for load/create/record/approve/cancel stock-count work.
- Create: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.stock-count.test.tsx`
  - Workspace integration flow for board-driven reviewed stock-count lifecycle.
- Create: `apps/store-desktop/src/control-plane/StoreStockCountSection.tsx`
  - Dedicated desktop stock-count UI.
- Create: `apps/store-desktop/src/control-plane/StoreStockCountSection.test.tsx`
  - Section rendering and blind-count visibility coverage.
- Modify: `apps/store-desktop/src/control-plane/client.ts`
  - Add stock-count desktop client helpers.
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
  - Add stock-count state and delegate side effects to `storeStockCountActions.ts`.
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx`
  - Mount the new stock-count section.
- Modify: `docs/WORKLOG.md`
  - Record the slice after verification.

### Task 1: Add Desktop Stock-Count Client Coverage And Helpers

**Files:**
- Create: `apps/store-desktop/src/control-plane/client.stock-count.test.ts`
- Modify: `apps/store-desktop/src/control-plane/client.ts`
- Test: `apps/store-desktop/src/control-plane/client.stock-count.test.ts`

- [ ] **Step 1: Write the failing client test**

```ts
/* @vitest-environment jsdom */
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import type {
  ControlPlaneStockCountApproval,
  ControlPlaneStockCountBoard,
  ControlPlaneStockCountReviewSession,
} from '@store/types';
import { storeControlPlaneClient } from './client';

type MockResponse = { ok: boolean; status: number; json: () => Promise<unknown> };
const jsonResponse = (body: unknown, status = 200): MockResponse => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => body,
});

describe('storeControlPlaneClient stock count reviewed-session routes', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    globalThis.fetch = vi.fn() as typeof fetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  test('loads the stock-count board', async () => {
    const board: ControlPlaneStockCountBoard = {
      branch_id: 'branch-1',
      open_count: 1,
      counted_count: 0,
      approved_count: 0,
      canceled_count: 0,
      records: [
        {
          stock_count_session_id: 'scs-1',
          session_number: 'SCS-BLRFLAGSHIP-0001',
          product_id: 'product-1',
          product_name: 'Classic Tea',
          sku_code: 'tea-classic-250g',
          status: 'OPEN',
          expected_quantity: null,
          counted_quantity: null,
          variance_quantity: null,
          note: 'Aisle recount',
          review_note: null,
        },
      ],
    };
    vi.mocked(globalThis.fetch).mockResolvedValueOnce(jsonResponse(board) as never);

    const result = await storeControlPlaneClient.getStockCountBoard('access-token', 'tenant-1', 'branch-1');

    expect(result).toEqual(board);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/v1/tenants/tenant-1/branches/branch-1/stock-count-board'),
      expect.objectContaining({
        headers: expect.objectContaining({
          authorization: 'Bearer access-token',
          'content-type': 'application/json',
        }),
      }),
    );
  });

  test('creates, records, approves, and cancels a reviewed stock-count session', async () => {
    const openSession: ControlPlaneStockCountReviewSession = {
      id: 'scs-1',
      tenant_id: 'tenant-1',
      branch_id: 'branch-1',
      product_id: 'product-1',
      session_number: 'SCS-BLRFLAGSHIP-0001',
      status: 'OPEN',
      expected_quantity: null,
      counted_quantity: null,
      variance_quantity: null,
      note: 'Aisle recount',
      review_note: null,
    };
    const countedSession: ControlPlaneStockCountReviewSession = {
      ...openSession,
      status: 'COUNTED',
      expected_quantity: 12,
      counted_quantity: 10,
      variance_quantity: -2,
    };
    const approval: ControlPlaneStockCountApproval = {
      session: { ...countedSession, status: 'APPROVED', review_note: 'Approved after review' },
      stock_count: {
        id: 'count-1',
        tenant_id: 'tenant-1',
        branch_id: 'branch-1',
        product_id: 'product-1',
        counted_quantity: 10,
        expected_quantity: 12,
        variance_quantity: -2,
        note: 'Aisle recount',
        closing_stock: 10,
      },
    };

    vi.mocked(globalThis.fetch)
      .mockResolvedValueOnce(jsonResponse(openSession) as never)
      .mockResolvedValueOnce(jsonResponse(countedSession) as never)
      .mockResolvedValueOnce(jsonResponse(approval) as never)
      .mockResolvedValueOnce(jsonResponse({ ...countedSession, status: 'CANCELED', review_note: 'Canceled after recount' }) as never);

    await storeControlPlaneClient.createStockCountSession('access-token', 'tenant-1', 'branch-1', {
      product_id: 'product-1',
      note: 'Aisle recount',
    });
    await storeControlPlaneClient.recordStockCountSession('access-token', 'tenant-1', 'branch-1', 'scs-1', {
      counted_quantity: 10,
      note: 'Blind count complete',
    });
    await storeControlPlaneClient.approveStockCountSession('access-token', 'tenant-1', 'branch-1', 'scs-1', {
      review_note: 'Approved after review',
    });
    await storeControlPlaneClient.cancelStockCountSession('access-token', 'tenant-1', 'branch-1', 'scs-1', {
      review_note: 'Canceled after recount',
    });
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test --workspace @store/store-desktop -- client.stock-count.test.ts`
Expected: FAIL with `storeControlPlaneClient.getStockCountBoard is not a function` and similar missing helper errors.

- [ ] **Step 3: Write minimal client implementation**

```ts
getStockCountBoard(accessToken: string, tenantId: string, branchId: string) {
  return request<ControlPlaneStockCountBoard>(
    `/v1/tenants/${tenantId}/branches/${branchId}/stock-count-board`,
    undefined,
    accessToken,
  );
},
createStockCountSession(
  accessToken: string,
  tenantId: string,
  branchId: string,
  payload: { product_id: string; note?: string | null },
) {
  return request<ControlPlaneStockCountReviewSession>(
    `/v1/tenants/${tenantId}/branches/${branchId}/stock-count-sessions`,
    { method: 'POST', body: JSON.stringify(payload) },
    accessToken,
  );
},
recordStockCountSession(
  accessToken: string,
  tenantId: string,
  branchId: string,
  stockCountSessionId: string,
  payload: { counted_quantity: number; note?: string | null },
) {
  return request<ControlPlaneStockCountReviewSession>(
    `/v1/tenants/${tenantId}/branches/${branchId}/stock-count-sessions/${stockCountSessionId}/record`,
    { method: 'POST', body: JSON.stringify(payload) },
    accessToken,
  );
},
approveStockCountSession(
  accessToken: string,
  tenantId: string,
  branchId: string,
  stockCountSessionId: string,
  payload: { review_note?: string | null },
) {
  return request<ControlPlaneStockCountApproval>(
    `/v1/tenants/${tenantId}/branches/${branchId}/stock-count-sessions/${stockCountSessionId}/approve`,
    { method: 'POST', body: JSON.stringify(payload) },
    accessToken,
  );
},
cancelStockCountSession(
  accessToken: string,
  tenantId: string,
  branchId: string,
  stockCountSessionId: string,
  payload: { review_note?: string | null },
) {
  return request<ControlPlaneStockCountReviewSession>(
    `/v1/tenants/${tenantId}/branches/${branchId}/stock-count-sessions/${stockCountSessionId}/cancel`,
    { method: 'POST', body: JSON.stringify(payload) },
    accessToken,
  );
},
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm run test --workspace @store/store-desktop -- client.stock-count.test.ts`
Expected: PASS with all stock-count client route assertions green.

- [ ] **Step 5: Commit**

```bash
git add apps/store-desktop/src/control-plane/client.ts apps/store-desktop/src/control-plane/client.stock-count.test.ts
git commit -m "test: add desktop stock count client coverage"
```

### Task 2: Extract Desktop Stock-Count Actions And Workspace State

**Files:**
- Create: `apps/store-desktop/src/control-plane/storeStockCountActions.ts`
- Create: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.stock-count.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts`
- Test: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.stock-count.test.tsx`

- [ ] **Step 1: Write the failing workspace flow test**

```tsx
/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, test, vi } from 'vitest';
import { useStoreRuntimeWorkspace } from './useStoreRuntimeWorkspace';

function WorkspaceHarness() {
  const workspace = useStoreRuntimeWorkspace();
  return (
    <div>
      <input aria-label="Korsenex token" value={workspace.korsenexToken} onChange={(e) => workspace.setKorsenexToken(e.target.value)} />
      <button onClick={() => void workspace.startSession()}>Start runtime session</button>
      <button onClick={() => void workspace.loadStockCountBoard()}>Load stock-count board</button>
      <button onClick={() => void workspace.createStockCountSession()}>Create stock-count session</button>
      <button onClick={() => void workspace.recordStockCountSession()}>Record stock-count session</button>
      <button onClick={() => void workspace.approveStockCountSession()}>Approve stock-count session</button>
      <button onClick={() => void workspace.cancelStockCountSession()}>Cancel stock-count session</button>
      <input aria-label="Count note" value={workspace.stockCountNote} onChange={(e) => workspace.setStockCountNote(e.target.value)} />
      <input aria-label="Blind counted quantity" value={workspace.blindCountedQuantity} onChange={(e) => workspace.setBlindCountedQuantity(e.target.value)} />
      <input aria-label="Stock-count review note" value={workspace.stockCountReviewNote} onChange={(e) => workspace.setStockCountReviewNote(e.target.value)} />
      <output>{workspace.stockCountBoard ? `Board open -> ${workspace.stockCountBoard.open_count}` : 'No board'}</output>
      <output>{workspace.activeStockCountSession ? `Session ${workspace.activeStockCountSession.session_number} -> ${workspace.activeStockCountSession.status}` : 'No active session'}</output>
      <output>{workspace.latestApprovedStockCount ? `Latest stock count -> ${workspace.latestApprovedStockCount.counted_quantity}` : 'No latest stock count'}</output>
    </div>
  );
}

test('runs desktop reviewed stock-count flow end-to-end', async () => {
  render(<WorkspaceHarness />);
  fireEvent.change(screen.getByLabelText('Korsenex token'), { target: { value: 'stub:sub=stock-1;email=stock@acme.local;name=Stock Clerk' } });
  fireEvent.click(screen.getByText('Start runtime session'));
  fireEvent.click(screen.getByText('Load stock-count board'));
  await waitFor(() => expect(screen.getByText('Board open -> 0')).toBeInTheDocument());
  fireEvent.change(screen.getByLabelText('Count note'), { target: { value: 'Aisle recount' } });
  fireEvent.click(screen.getByText('Create stock-count session'));
  await waitFor(() => expect(screen.getByText(/Session SCS-BLRFLAGSHIP-0001 -> OPEN/)).toBeInTheDocument());
  fireEvent.change(screen.getByLabelText('Blind counted quantity'), { target: { value: '10' } });
  fireEvent.click(screen.getByText('Record stock-count session'));
  await waitFor(() => expect(screen.getByText(/Session SCS-BLRFLAGSHIP-0001 -> COUNTED/)).toBeInTheDocument());
  fireEvent.change(screen.getByLabelText('Stock-count review note'), { target: { value: 'Approved after review' } });
  fireEvent.click(screen.getByText('Approve stock-count session'));
  await waitFor(() => expect(screen.getByText('Latest stock count -> 10')).toBeInTheDocument());
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.stock-count.test.tsx`
Expected: FAIL because stock-count workspace state/actions do not exist yet.

- [ ] **Step 3: Implement a focused stock-count action helper**

```ts
// apps/store-desktop/src/control-plane/storeStockCountActions.ts
import { startTransition } from 'react';
import type { ControlPlaneStockCount, ControlPlaneStockCountBoard, ControlPlaneStockCountReviewSession } from '@store/types';
import { storeControlPlaneClient } from './client';

export async function runLoadStockCountBoard(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: (value: string) => void;
  setStockCountBoard: (value: ControlPlaneStockCountBoard | null) => void;
}) {
  const { accessToken, tenantId, branchId, setIsBusy, setErrorMessage, setStockCountBoard } = params;
  setIsBusy(true);
  setErrorMessage('');
  try {
    const board = await storeControlPlaneClient.getStockCountBoard(accessToken, tenantId, branchId);
    startTransition(() => setStockCountBoard(board));
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to load stock-count board');
  } finally {
    setIsBusy(false);
  }
}

export async function runCreateStockCountSession(params: {
  accessToken: string;
  tenantId: string;
  branchId: string;
  productId: string;
  note: string;
  setIsBusy: (value: boolean) => void;
  setErrorMessage: (value: string) => void;
  setActiveStockCountSession: (value: ControlPlaneStockCountReviewSession | null) => void;
  setStockCountBoard: (value: ControlPlaneStockCountBoard | null) => void;
}) {
  const { accessToken, tenantId, branchId, productId, note, setIsBusy, setErrorMessage, setActiveStockCountSession, setStockCountBoard } = params;
  setIsBusy(true);
  setErrorMessage('');
  try {
    const session = await storeControlPlaneClient.createStockCountSession(accessToken, tenantId, branchId, {
      product_id: productId,
      note: note || null,
    });
    const board = await storeControlPlaneClient.getStockCountBoard(accessToken, tenantId, branchId);
    startTransition(() => {
      setActiveStockCountSession(session);
      setStockCountBoard(board);
    });
  } catch (error) {
    setErrorMessage(error instanceof Error ? error.message : 'Unable to open stock-count session');
  } finally {
    setIsBusy(false);
  }
}
```

- [ ] **Step 4: Wire stock-count state into the workspace without growing the file’s responsibilities**

```ts
// useStoreRuntimeWorkspace.ts
const [stockCountBoard, setStockCountBoard] = useState<ControlPlaneStockCountBoard | null>(null);
const [activeStockCountSession, setActiveStockCountSession] = useState<ControlPlaneStockCountReviewSession | null>(null);
const [latestApprovedStockCount, setLatestApprovedStockCount] = useState<ControlPlaneStockCount | null>(null);
const [selectedStockCountProductId, setSelectedStockCountProductId] = useState('');
const [stockCountNote, setStockCountNote] = useState('');
const [blindCountedQuantity, setBlindCountedQuantity] = useState('');
const [stockCountReviewNote, setStockCountReviewNote] = useState('');

async function loadStockCountBoard() {
  if (!accessToken || !tenantId || !branchId) return;
  await runLoadStockCountBoard({
    accessToken,
    tenantId,
    branchId,
    setIsBusy,
    setErrorMessage,
    setStockCountBoard,
  });
}

function selectStockCountProduct(productId: string) {
  setSelectedStockCountProductId(productId);
}

async function createStockCountSession() {
  if (!accessToken || !tenantId || !branchId || !selectedStockCountProductId) return;
  await runCreateStockCountSession({
    accessToken,
    tenantId,
    branchId,
    productId: selectedStockCountProductId,
    note: stockCountNote,
    setIsBusy,
    setErrorMessage,
    setActiveStockCountSession,
    setStockCountBoard,
  });
}
```

- [ ] **Step 5: Run workspace tests to verify they pass**

Run: `npm run test --workspace @store/store-desktop -- StoreRuntimeWorkspace.stock-count.test.tsx`
Expected: PASS with create, record, approve, and cancel lifecycle assertions green.

- [ ] **Step 6: Commit**

```bash
git add apps/store-desktop/src/control-plane/storeStockCountActions.ts apps/store-desktop/src/control-plane/useStoreRuntimeWorkspace.ts apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.stock-count.test.tsx
git commit -m "feat: add desktop stock count workspace actions"
```

### Task 3: Add The Desktop Stock-Count Section And Mount It

**Files:**
- Create: `apps/store-desktop/src/control-plane/StoreStockCountSection.tsx`
- Create: `apps/store-desktop/src/control-plane/StoreStockCountSection.test.tsx`
- Modify: `apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx`
- Modify: `docs/WORKLOG.md`
- Test: `apps/store-desktop/src/control-plane/StoreStockCountSection.test.tsx`

- [ ] **Step 1: Write the failing section test**

```tsx
/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import { StoreStockCountSection } from './StoreStockCountSection';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

function buildWorkspace(overrides: Partial<StoreRuntimeWorkspaceState> = {}): StoreRuntimeWorkspaceState {
  return {
    isBusy: false,
    isSessionLive: true,
    branchId: 'branch-1',
    stockCountBoard: null,
    activeStockCountSession: null,
    latestApprovedStockCount: null,
    selectedStockCountProductId: 'product-1',
    stockCountNote: '',
    blindCountedQuantity: '10',
    stockCountReviewNote: '',
    loadStockCountBoard: vi.fn(async () => {}),
    createStockCountSession: vi.fn(async () => {}),
    recordStockCountSession: vi.fn(async () => {}),
    approveStockCountSession: vi.fn(async () => {}),
    cancelStockCountSession: vi.fn(async () => {}),
    setSelectedStockCountProductId: vi.fn(),
    setStockCountNote: vi.fn(),
    setBlindCountedQuantity: vi.fn(),
    setStockCountReviewNote: vi.fn(),
    ...overrides,
  } as unknown as StoreRuntimeWorkspaceState;
}

test('keeps expected quantity hidden while session is open and reveals it when counted', () => {
  const openWorkspace = buildWorkspace({
    stockCountBoard: {
      branch_id: 'branch-1',
      open_count: 1,
      counted_count: 0,
      approved_count: 0,
      canceled_count: 0,
      records: [{ stock_count_session_id: 'scs-1', session_number: 'SCS-BLRFLAGSHIP-0001', product_id: 'product-1', product_name: 'Classic Tea', sku_code: 'tea-classic-250g', status: 'OPEN', expected_quantity: null, counted_quantity: null, variance_quantity: null, note: 'Aisle recount', review_note: null }],
    },
    activeStockCountSession: {
      id: 'scs-1',
      tenant_id: 'tenant-acme',
      branch_id: 'branch-1',
      product_id: 'product-1',
      session_number: 'SCS-BLRFLAGSHIP-0001',
      status: 'OPEN',
      expected_quantity: null,
      counted_quantity: null,
      variance_quantity: null,
      note: 'Aisle recount',
      review_note: null,
    },
  });

  const { rerender } = render(<StoreStockCountSection workspace={openWorkspace} />);
  expect(screen.queryByText('Expected quantity')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Record blind count' }));
  expect(openWorkspace.recordStockCountSession).toHaveBeenCalledTimes(1);

  const countedWorkspace = buildWorkspace({
    stockCountBoard: {
      branch_id: 'branch-1',
      open_count: 0,
      counted_count: 1,
      approved_count: 0,
      canceled_count: 0,
      records: [{ stock_count_session_id: 'scs-1', session_number: 'SCS-BLRFLAGSHIP-0001', product_id: 'product-1', product_name: 'Classic Tea', sku_code: 'tea-classic-250g', status: 'COUNTED', expected_quantity: 12, counted_quantity: 10, variance_quantity: -2, note: 'Aisle recount', review_note: null }],
    },
    activeStockCountSession: {
      id: 'scs-1',
      tenant_id: 'tenant-acme',
      branch_id: 'branch-1',
      product_id: 'product-1',
      session_number: 'SCS-BLRFLAGSHIP-0001',
      status: 'COUNTED',
      expected_quantity: 12,
      counted_quantity: 10,
      variance_quantity: -2,
      note: 'Aisle recount',
      review_note: null,
    },
  });

  rerender(<StoreStockCountSection workspace={countedWorkspace} />);
  expect(screen.getByText('Expected quantity')).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test --workspace @store/store-desktop -- StoreStockCountSection.test.tsx`
Expected: FAIL because `StoreStockCountSection` does not exist yet.

- [ ] **Step 3: Implement the stock-count section and mount it**

```tsx
// StoreStockCountSection.tsx
import { ActionButton, DetailList, FormField, SectionCard, StatusBadge } from '@store/ui';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';

export function StoreStockCountSection({ workspace }: { workspace: StoreRuntimeWorkspaceState }) {
  const isOpenSession = workspace.activeStockCountSession?.status === 'OPEN';
  const isCountedSession = workspace.activeStockCountSession?.status === 'COUNTED';
  const selectedRecord = workspace.stockCountBoard?.records.find(
    (record) => record.product_id === workspace.selectedStockCountProductId,
  ) ?? workspace.stockCountBoard?.records[0] ?? null;

  return (
    <SectionCard eyebrow="Blind count workflow" title="Branch stock count">
      <ActionButton onClick={() => void workspace.loadStockCountBoard()} disabled={workspace.isBusy || !workspace.isSessionLive || !workspace.branchId}>
        Load stock-count board
      </ActionButton>
      <ul>
        {workspace.stockCountBoard?.records.length ? (
          workspace.stockCountBoard.records.map((record) => (
            <li key={record.stock_count_session_id}>
              <button type="button" onClick={() => workspace.setSelectedStockCountProductId(record.product_id)}>
                Select
              </button>
              {record.session_number} :: {record.product_name} :: {record.status}
              {record.variance_quantity == null ? '' : ` :: variance ${record.variance_quantity}`}
            </li>
          ))
        ) : (
          <li>No stock count sessions recorded yet.</li>
        )}
      </ul>
      <FormField id="runtime-stock-count-note" label="Count note" value={workspace.stockCountNote} onChange={workspace.setStockCountNote} />
      {selectedRecord ? <DetailList items={[{ label: 'Selected product', value: selectedRecord.product_name }]} /> : null}
      <ActionButton onClick={() => void workspace.createStockCountSession()} disabled={workspace.isBusy || !workspace.selectedStockCountProductId}>
        Open stock count session
      </ActionButton>
      {isOpenSession ? <ActionButton onClick={() => void workspace.recordStockCountSession()}>Record blind count</ActionButton> : null}
      {isCountedSession ? <ActionButton onClick={() => void workspace.approveStockCountSession()}>Approve stock count session</ActionButton> : null}
    </SectionCard>
  );
}
```

- [ ] **Step 4: Run section and integration verification**

Run:
- `npm run test --workspace @store/store-desktop -- StoreStockCountSection.test.tsx StoreRuntimeWorkspace.stock-count.test.tsx client.stock-count.test.ts`
- `npm run typecheck --workspace @store/store-desktop`
- `npm run build --workspace @store/store-desktop`

Expected:
- All three stock-count tests PASS
- TypeScript exits 0
- Vite build exits 0

- [ ] **Step 5: Update worklog and commit**

```md
- Added Store Desktop reviewed stock-count sessions with a dedicated board-driven section, client route coverage, and extracted workspace actions.
```

```bash
git add apps/store-desktop/src/control-plane/StoreStockCountSection.tsx apps/store-desktop/src/control-plane/StoreStockCountSection.test.tsx apps/store-desktop/src/control-plane/StoreRuntimeWorkspace.tsx docs/WORKLOG.md
git commit -m "feat: add desktop reviewed stock count workflow"
```

## Self-Review

- Spec coverage: the three tasks cover client helpers, workspace state/actions, dedicated section UI, blind-count visibility, approval/cancel lifecycle, and worklog update. No spec requirement is left without a task.
- Placeholder scan: no `TODO`, `TBD`, or “similar to” placeholders remain. Every task includes concrete file paths, code, and commands.
- Type consistency: the plan consistently uses `stockCountBoard`, `activeStockCountSession`, `latestApprovedStockCount`, `stockCountNote`, `blindCountedQuantity`, and `stockCountReviewNote`, matching the spec naming.
