/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import { StoreThemeProvider } from '@store/ui';
import { PlatformAdminAuthEntrySurface } from './PlatformAdminAuthEntrySurface';

function createProps(overrides?: Partial<Parameters<typeof PlatformAdminAuthEntrySurface>[0]>) {
  return {
    errorMessage: '',
    isBusy: false,
    korsenexToken: '',
    onChangeKorsenexToken: vi.fn(),
    onSignIn: vi.fn(),
    onStartSession: vi.fn(),
    planCount: 0,
    sessionState: 'signed_out' as const,
    showLocalDeveloperControls: false,
    tenantCount: 0,
    ...overrides,
  };
}

function renderWithTheme(props: Parameters<typeof PlatformAdminAuthEntrySurface>[0]) {
  return render(
    <StoreThemeProvider storageKey="platform-auth-entry.test.theme">
      <PlatformAdminAuthEntrySurface {...props} />
    </StoreThemeProvider>,
  );
}

describe('PlatformAdminAuthEntrySurface', () => {
  test('shows platform sign-in by default', () => {
    const props = createProps();
    renderWithTheme(props);

    expect(screen.getByRole('heading', { name: 'Platform sign-in' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Sign in with Korsenex' }));
    expect(props.onSignIn).toHaveBeenCalledTimes(1);
  });

  test('shows restoring posture while the platform session is being recovered', () => {
    renderWithTheme(createProps({ isBusy: true, sessionState: 'restoring' }));

    expect(screen.getByRole('heading', { name: 'Restoring control plane session' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Restoring session…' })).toBeDisabled();
  });

  test('shows recovery guidance for expired sessions', () => {
    renderWithTheme(createProps({ errorMessage: 'Refresh failed', sessionState: 'expired' }));

    expect(screen.getByRole('heading', { name: 'Platform session expired' })).toBeInTheDocument();
    expect(screen.getByText('Refresh failed')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign in again' })).toBeEnabled();
  });

  test('can expose developer bootstrap controls without removing the real sign-in CTA', () => {
    const props = createProps({
      korsenexToken: 'stub:sub=platform-1;email=admin@store.local;name=Platform Admin',
      showLocalDeveloperControls: true,
    });
    renderWithTheme(props);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=platform-2;email=ops@store.local;name=Ops Admin' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start control plane session' }));

    expect(props.onChangeKorsenexToken).toHaveBeenCalledWith('stub:sub=platform-2;email=ops@store.local;name=Ops Admin');
    expect(props.onStartSession).toHaveBeenCalledTimes(1);
    expect(screen.getAllByRole('button', { name: 'Sign in with Korsenex' }).length).toBeGreaterThan(0);
  });
});
