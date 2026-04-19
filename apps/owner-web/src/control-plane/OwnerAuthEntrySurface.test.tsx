/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';
import { StoreThemeProvider } from '@store/ui';
import { OwnerAuthEntrySurface } from './OwnerAuthEntrySurface';

function createProps(overrides?: Partial<Parameters<typeof OwnerAuthEntrySurface>[0]>) {
  return {
    branchCount: 0,
    errorMessage: '',
    isBusy: false,
    korsenexToken: '',
    onChangeKorsenexToken: vi.fn(),
    onSignIn: vi.fn(),
    onStartSession: vi.fn(),
    onboardingStatus: 'PENDING',
    sessionState: 'signed_out' as const,
    showLocalDeveloperControls: false,
    ...overrides,
  };
}

function renderWithTheme(props: Parameters<typeof OwnerAuthEntrySurface>[0]) {
  return render(
    <StoreThemeProvider storageKey="owner-auth-entry.test.theme">
      <OwnerAuthEntrySurface {...props} />
    </StoreThemeProvider>,
  );
}

describe('OwnerAuthEntrySurface', () => {
  test('shows the real Korsenex sign-in entry by default', () => {
    const props = createProps();
    renderWithTheme(props);

    expect(screen.getByRole('heading', { name: 'Owner sign-in' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Sign in with Korsenex' }));
    expect(props.onSignIn).toHaveBeenCalledTimes(1);
    expect(screen.queryByLabelText('Korsenex token')).not.toBeInTheDocument();
  });

  test('shows restoring posture while session recovery is in progress', () => {
    renderWithTheme(createProps({ isBusy: true, sessionState: 'restoring' }));

    expect(screen.getByRole('heading', { name: 'Restoring owner session' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Restoring session…' })).toBeDisabled();
  });

  test('shows recovery guidance for expired sessions', () => {
    renderWithTheme(createProps({ errorMessage: 'Refresh failed', sessionState: 'expired' }));

    expect(screen.getByRole('heading', { name: 'Owner session expired' })).toBeInTheDocument();
    expect(screen.getByText('Refresh failed')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign in again' })).toBeEnabled();
  });

  test('can expose local developer bootstrap controls without replacing the real sign-in CTA', () => {
    const props = createProps({
      korsenexToken: 'stub:sub=owner-1;email=owner@acme.local;name=Acme Owner',
      showLocalDeveloperControls: true,
    });
    renderWithTheme(props);

    fireEvent.change(screen.getByLabelText('Korsenex token'), {
      target: { value: 'stub:sub=owner-2;email=owner@beta.local;name=Beta Owner' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Start owner session' }));

    expect(props.onChangeKorsenexToken).toHaveBeenCalledWith('stub:sub=owner-2;email=owner@beta.local;name=Beta Owner');
    expect(props.onStartSession).toHaveBeenCalledTimes(1);
    expect(screen.getAllByRole('button', { name: 'Sign in with Korsenex' }).length).toBeGreaterThan(0);
  });
});
