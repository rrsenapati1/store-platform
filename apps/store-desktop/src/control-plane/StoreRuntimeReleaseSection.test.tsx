/* @vitest-environment jsdom */
import '@testing-library/jest-dom/vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, test, vi } from 'vitest';
import { StoreRuntimeReleaseSection } from './StoreRuntimeReleaseSection';

const checkMock = vi.fn();
const installMock = vi.fn();

vi.mock('./useStoreRuntimeShellStatus', () => ({
  useStoreRuntimeShellStatus: vi.fn(() => ({
    runtimeShellError: null,
    runtimeShellStatus: {
      runtime_kind: 'packaged_desktop',
      runtime_label: 'Store Desktop packaged runtime',
      bridge_state: 'ready',
      app_version: '0.1.0',
      hostname: 'COUNTER-01',
      operating_system: 'windows',
      architecture: 'x86_64',
      installation_id: 'install-1',
      claim_code: 'STORE-INSTALL1',
      runtime_home: 'C:/StoreRuntime',
      cache_db_path: 'C:/StoreRuntime/store-runtime-cache.sqlite3',
      control_plane_base_url: 'https://control.acme.local',
      release_environment: 'staging',
      release_profile_source: 'bundled',
      updater_endpoint: 'https://updates.acme.local/latest.json',
      updater_pubkey_configured: true,
      hub_service_state: null,
      hub_service_url: null,
      hub_manifest_url: null,
    },
  })),
}));

vi.mock('../runtime-updater/storeRuntimeUpdater', () => ({
  createResolvedStoreRuntimeUpdater: vi.fn(() => ({
    check: checkMock,
    install: installMock,
  })),
}));

afterEach(() => {
  checkMock.mockReset();
  installMock.mockReset();
});

describe('store runtime release section', () => {
  test('renders packaged release posture and available update details', async () => {
    checkMock.mockResolvedValue({
      state: 'update_available',
      current_version: '0.1.0',
      release_environment: 'staging',
      updater_endpoint: 'https://updates.acme.local/latest.json',
      update_version: '0.1.1',
      notes: 'Critical release',
      pub_date: '2026-04-14T00:00:00Z',
      error: null,
    });
    installMock.mockResolvedValue({
      state: 'installed',
      current_version: '0.1.0',
      release_environment: 'staging',
      updater_endpoint: 'https://updates.acme.local/latest.json',
      installed_version: '0.1.1',
      error: null,
    });

    render(<StoreRuntimeReleaseSection />);

    await waitFor(() => expect(screen.getByText('staging')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'Check for updates' }));
    await waitFor(() => expect(screen.getByText('Available 0.1.1')).toBeInTheDocument());
    expect(screen.getByText(/Critical release/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Install pending update' }));
    await waitFor(() => expect(screen.getByText('Installed 0.1.1')).toBeInTheDocument());
  });
});
