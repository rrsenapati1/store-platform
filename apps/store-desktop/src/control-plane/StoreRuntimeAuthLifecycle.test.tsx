/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { StoreThemeProvider } from '@store/ui';
import { describe, expect, test, vi } from 'vitest';
import type { StoreRuntimeWorkspaceState } from './useStoreRuntimeWorkspace';
import { StoreRuntimeLayout } from './storeRuntimeLayout';

function buildWorkspace(overrides: Partial<StoreRuntimeWorkspaceState> = {}): StoreRuntimeWorkspaceState {
  return {
    actor: {
      user_id: 'user-cashier',
      email: 'cashier@acme.local',
      full_name: 'Counter Cashier',
      is_platform_admin: false,
      tenant_memberships: [],
      branch_memberships: [{ tenant_id: 'tenant-acme', branch_id: 'branch-1', role_name: 'cashier', status: 'ACTIVE' }],
    },
    accessToken: 'session-token',
    activeCashierSession: null,
    activeAttendanceSession: null,
    activeShiftSession: null,
    attendanceClockInNote: '',
    attendanceClockOutNote: '',
    attendanceSessions: [],
    branchId: 'branch-1',
    branches: [{ branch_id: 'branch-1', tenant_id: 'tenant-acme', name: 'Bengaluru Flagship', branch_code: 'blr-1', timezone: 'Asia/Kolkata', currency_code: 'INR', status: 'ACTIVE' }],
    branchRuntimePolicy: {
      require_attendance_for_cashier: true,
      require_shift_for_attendance: false,
      require_assigned_staff_for_device: true,
      allow_offline_sales: true,
      max_pending_offline_sales: 25,
    },
    cashierOpeningFloatAmount: '',
    cashierOpeningNote: '',
    cashierClosingNote: '',
    errorMessage: '',
    hasLoadedLocalAuth: true,
    isBusy: false,
    isSessionLive: true,
    shiftClosingNote: '',
    shiftName: '',
    shiftOpeningNote: '',
    shiftSessions: [],
    requiresLocalUnlock: false,
    requiresPinEnrollment: false,
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
    runtimeHostname: 'localhost',
    runtimeShellKind: 'browser_web',
    runtimeShellLabel: 'Browser web runtime',
    runtimeSessionStatus: 'ready',
    selectedRuntimeDeviceId: 'device-1',
    sessionExpiresAt: '2099-01-01T00:00:00Z',
    closeAttendanceSession: vi.fn(async () => {}),
    closeCashierSession: vi.fn(async () => {}),
    closeShiftSession: vi.fn(async () => {}),
    loadAttendanceSessions: vi.fn(async () => {}),
    loadCashierSessions: vi.fn(async () => {}),
    loadShiftSessions: vi.fn(async () => {}),
    openAttendanceSession: vi.fn(async () => {}),
    openCashierSession: vi.fn(async () => {}),
    openShiftSession: vi.fn(async () => {}),
    setAttendanceClockInNote: vi.fn(),
    setAttendanceClockOutNote: vi.fn(),
    setCashierClosingNote: vi.fn(),
    setCashierOpeningFloatAmount: vi.fn(),
    setCashierOpeningNote: vi.fn(),
    setShiftClosingNote: vi.fn(),
    setShiftName: vi.fn(),
    setShiftOpeningNote: vi.fn(),
    signOut: vi.fn(async () => {}),
    refreshRuntimeSession: vi.fn(async () => {}),
    supportsDeveloperSessionBootstrap: true,
    ...overrides,
  } as unknown as StoreRuntimeWorkspaceState;
}

describe('StoreRuntime auth lifecycle shell', () => {
  test('surfaces explicit recovery posture in the runtime status strip', () => {
    render(
      <StoreThemeProvider storageKey="store-desktop.theme.mode">
        <StoreRuntimeLayout
          workspace={buildWorkspace({
            actor: null,
            accessToken: '',
            isSessionLive: false,
            runtimeSessionStatus: 'revoked',
            supportsDeveloperSessionBootstrap: false,
            runtimeShellKind: 'packaged_desktop',
          })}
          activeScreen="entry"
          visibleScreens={['entry']}
          onSelectScreen={vi.fn()}
          runtimeReady={false}
        />
      </StoreThemeProvider>,
    );

    expect(screen.getByText('Revoked')).toBeInTheDocument();
  });

  test('keeps sign-out available from the live runtime shell', () => {
    const signOut = vi.fn(async () => {});

    render(
      <StoreThemeProvider storageKey="store-desktop.theme.mode">
        <StoreRuntimeLayout
          workspace={buildWorkspace({ signOut })}
          activeScreen="entry"
          visibleScreens={['entry', 'sell']}
          onSelectScreen={vi.fn()}
          runtimeReady
        />
      </StoreThemeProvider>,
    );

    fireEvent.click(screen.getAllByRole('button', { name: 'Sign out' })[0]);

    expect(signOut).toHaveBeenCalledTimes(1);
  });
});
