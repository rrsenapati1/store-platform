/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import type { ControlPlaneAttendanceSession, ControlPlaneCashierSession } from '@store/types';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';
import { StoreRuntimeEntrySurface } from './storeRuntimeEntrySurface';

function createAttendanceSession(
  overrides: Partial<ControlPlaneAttendanceSession> = {},
): ControlPlaneAttendanceSession {
  return {
    id: 'attendance-session-1',
    tenant_id: 'tenant-acme',
    branch_id: 'branch-1',
    shift_session_id: null,
    device_registration_id: 'device-1',
    device_name: 'Counter Desktop 1',
    device_code: 'counter-1',
    staff_profile_id: 'staff-1',
    staff_full_name: 'Counter Cashier',
    runtime_user_id: 'user-cashier',
    opened_by_user_id: 'user-cashier',
    closed_by_user_id: null,
    status: 'OPEN',
    attendance_number: 'ATTD-BLRFLAGSHIP-0001',
    clock_in_note: null,
    clock_out_note: null,
    force_close_reason: null,
    opened_at: '2026-04-19T10:00:00.000Z',
    closed_at: null,
    last_activity_at: '2026-04-19T10:00:00.000Z',
    linked_cashier_sessions_count: 0,
    ...overrides,
  };
}

function createCashierSession(
  overrides: Partial<ControlPlaneCashierSession> = {},
): ControlPlaneCashierSession {
  return {
    id: 'cashier-session-1',
    tenant_id: 'tenant-acme',
    branch_id: 'branch-1',
    attendance_session_id: 'attendance-session-1',
    device_registration_id: 'device-1',
    device_name: 'Counter Desktop 1',
    device_code: 'counter-1',
    staff_profile_id: 'staff-1',
    staff_full_name: 'Counter Cashier',
    runtime_user_id: 'user-cashier',
    opened_by_user_id: 'user-cashier',
    closed_by_user_id: null,
    status: 'OPEN',
    session_number: 'CS-BLRFLAGSHIP-0001',
    opening_float_amount: 500,
    opening_note: null,
    closing_note: null,
    force_close_reason: null,
    opened_at: '2026-04-19T10:05:00.000Z',
    closed_at: null,
    last_activity_at: '2026-04-19T10:05:00.000Z',
    linked_sales_count: 0,
    linked_returns_count: 0,
    gross_billed_amount: 0,
    ...overrides,
  };
}

function buildWorkspace(overrides: Partial<StoreRuntimeWorkspaceState> = {}): StoreRuntimeWorkspaceState {
  return {
    actor: null,
    accessToken: null,
    isBusy: false,
    isSessionLive: false,
    supportsDeveloperSessionBootstrap: true,
    korsenexToken: '',
    setKorsenexToken: vi.fn(),
    startSession: vi.fn(async () => {}),
    refreshRuntimeSession: vi.fn(async () => {}),
    signOut: vi.fn(async () => {}),
    runtimeShellLabel: 'Browser web runtime',
    runtimeShellKind: 'browser_web',
    runtimeHostname: 'localhost',
    sessionExpiresAt: null,
    runtimeSessionStatus: 'signed_out',
    hasLoadedLocalAuth: true,
    requiresPinEnrollment: false,
    requiresLocalUnlock: false,
    activationCode: '',
    setActivationCode: vi.fn(),
    activateDesktopAccess: vi.fn(async () => {}),
    newPin: '',
    confirmPin: '',
    setNewPin: vi.fn(),
    setConfirmPin: vi.fn(),
    enrollRuntimePin: vi.fn(async () => {}),
    unlockPin: '',
    setUnlockPin: vi.fn(),
    unlockRuntimeWithPin: vi.fn(async () => {}),
    runtimeDevices: [
      {
        id: 'device-1',
        tenant_id: 'tenant-acme',
        branch_id: 'branch-1',
        device_name: 'Counter Desktop 1',
        device_code: 'counter-1',
        session_surface: 'store_desktop',
        status: 'ACTIVE',
        assigned_staff_profile_id: 'staff-1',
        assigned_staff_full_name: 'Counter Cashier',
      },
    ],
    selectedRuntimeDeviceId: 'device-1',
    activeAttendanceSession: null,
    attendanceSessions: [],
    attendanceClockInNote: '',
    attendanceClockOutNote: '',
    setAttendanceClockInNote: vi.fn(),
    setAttendanceClockOutNote: vi.fn(),
    openAttendanceSession: vi.fn(async () => {}),
    closeAttendanceSession: vi.fn(async () => {}),
    loadAttendanceSessions: vi.fn(async () => {}),
    activeCashierSession: null,
    cashierOpeningFloatAmount: '',
    cashierOpeningNote: '',
    cashierClosingNote: '',
    setCashierOpeningFloatAmount: vi.fn(),
    setCashierOpeningNote: vi.fn(),
    setCashierClosingNote: vi.fn(),
    openCashierSession: vi.fn(async () => {}),
    closeCashierSession: vi.fn(async () => {}),
    loadCashierSessions: vi.fn(async () => {}),
    branchRuntimePolicy: {
      require_attendance_for_cashier: true,
      require_shift_for_attendance: false,
      require_assigned_staff_for_device: true,
      allow_offline_sales: true,
      max_pending_offline_sales: 25,
    },
    activeShiftSession: null,
    shiftSessions: [],
    shiftName: '',
    shiftOpeningNote: '',
    shiftClosingNote: '',
    setShiftName: vi.fn(),
    setShiftOpeningNote: vi.fn(),
    setShiftClosingNote: vi.fn(),
    openShiftSession: vi.fn(async () => {}),
    closeShiftSession: vi.fn(async () => {}),
    loadShiftSessions: vi.fn(async () => {}),
    errorMessage: null,
    ...overrides,
  } as unknown as StoreRuntimeWorkspaceState;
}

describe('StoreRuntimeEntrySurface', () => {
  test('shows store access posture before the runtime session starts', () => {
    render(<StoreRuntimeEntrySurface workspace={buildWorkspace()} onResumeSelling={vi.fn()} />);

    expect(screen.getByRole('heading', { name: 'Store access' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Start runtime session' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Resume selling' })).toBeDisabled();
  });

  test('renders expired packaged-desktop recovery copy when a stored session has lapsed', () => {
    render(
      <StoreRuntimeEntrySurface
        workspace={buildWorkspace({
          runtimeShellKind: 'packaged_desktop',
          supportsDeveloperSessionBootstrap: false,
          runtimeSessionStatus: 'expired',
          requiresLocalUnlock: true,
          errorMessage: 'Stored runtime session expired. Sign in again.',
        })}
        onResumeSelling={vi.fn()}
      />,
    );

    expect(screen.getByRole('heading', { name: 'Runtime session expired' })).toBeInTheDocument();
    expect(screen.getByText(/Unlock this device to fetch a fresh session/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Unlock runtime' })).toBeInTheDocument();
  });

  test('renders revoked packaged-desktop activation copy after device access is invalidated', () => {
    render(
      <StoreRuntimeEntrySurface
        workspace={buildWorkspace({
          runtimeShellKind: 'packaged_desktop',
          supportsDeveloperSessionBootstrap: false,
          runtimeSessionStatus: 'revoked',
          requiresLocalUnlock: false,
          hasLoadedLocalAuth: true,
        })}
        onResumeSelling={vi.fn()}
      />,
    );

    expect(screen.getByRole('heading', { name: 'Runtime access revoked' })).toBeInTheDocument();
    expect(screen.getByText(/Ask the owner to issue a fresh activation code/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Activate desktop access' })).toBeInTheDocument();
  });

  test('requires attendance before register open when the branch runtime policy enforces it', () => {
    render(
      <StoreRuntimeEntrySurface
        workspace={buildWorkspace({
          actor: {
            user_id: 'user-cashier',
            email: 'cashier@acme.local',
            full_name: 'Counter Cashier',
            is_platform_admin: false,
            tenant_memberships: [],
            branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
          },
          isSessionLive: true,
          korsenexToken: 'stub:token',
        })}
        onResumeSelling={vi.fn()}
      />,
    );

    expect(screen.getByRole('button', { name: 'Clock in' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Open register' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Resume selling' })).toBeDisabled();
  });

  test('keeps register open disabled until the opening float gate is satisfied', () => {
    const { rerender } = render(
      <StoreRuntimeEntrySurface
        workspace={buildWorkspace({
          actor: {
            user_id: 'user-cashier',
            email: 'cashier@acme.local',
            full_name: 'Counter Cashier',
            is_platform_admin: false,
            tenant_memberships: [],
            branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
          },
          isSessionLive: true,
          korsenexToken: 'stub:token',
          activeAttendanceSession: createAttendanceSession(),
        })}
        onResumeSelling={vi.fn()}
      />,
    );

    expect(screen.getByRole('button', { name: 'Open register' })).toBeDisabled();

    rerender(
      <StoreRuntimeEntrySurface
        workspace={buildWorkspace({
          actor: {
            user_id: 'user-cashier',
            email: 'cashier@acme.local',
            full_name: 'Counter Cashier',
            is_platform_admin: false,
            tenant_memberships: [],
            branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
          },
          isSessionLive: true,
          korsenexToken: 'stub:token',
          cashierOpeningFloatAmount: '500',
          activeAttendanceSession: createAttendanceSession(),
        })}
        onResumeSelling={vi.fn()}
      />,
    );

    expect(screen.getByRole('button', { name: 'Open register' })).toBeEnabled();
  });

  test('switches to resume selling posture when a cashier session is already active', () => {
    render(
      <StoreRuntimeEntrySurface
        workspace={buildWorkspace({
          actor: {
            user_id: 'user-cashier',
            email: 'cashier@acme.local',
            full_name: 'Counter Cashier',
            is_platform_admin: false,
            tenant_memberships: [],
            branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
          },
          isSessionLive: true,
          korsenexToken: 'stub:token',
          activeAttendanceSession: createAttendanceSession(),
          activeCashierSession: createCashierSession(),
        })}
        onResumeSelling={vi.fn()}
      />,
    );

    expect(screen.getByRole('button', { name: 'Resume selling' })).toBeEnabled();
    expect(screen.queryByRole('button', { name: 'Open register' })).not.toBeInTheDocument();
  });
});
