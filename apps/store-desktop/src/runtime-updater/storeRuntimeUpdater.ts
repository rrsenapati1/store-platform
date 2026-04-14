import { invoke as tauriInvoke } from '@tauri-apps/api/core';
import { isNativeStoreRuntimeShellAvailable } from '../runtime-shell/storeRuntimeShell';

export interface StoreRuntimeUpdateCheckResult {
  state: 'unsupported' | 'unconfigured' | 'up_to_date' | 'update_available';
  current_version: string | null;
  release_environment: string | null;
  updater_endpoint: string | null;
  update_version: string | null;
  notes: string | null;
  pub_date: string | null;
  error: string | null;
}

export interface StoreRuntimeUpdateInstallResult {
  state: 'unsupported' | 'unconfigured' | 'up_to_date' | 'installed';
  current_version: string | null;
  release_environment: string | null;
  updater_endpoint: string | null;
  installed_version: string | null;
  error: string | null;
}

export interface StoreRuntimeUpdaterAdapter {
  check(): Promise<StoreRuntimeUpdateCheckResult>;
  install(): Promise<StoreRuntimeUpdateInstallResult>;
}

type Invoke = (command: string, payload?: Record<string, unknown>) => Promise<unknown>;

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function toCheckResult(value: unknown): StoreRuntimeUpdateCheckResult {
  if (!isObject(value)) {
    throw new Error('Native runtime updater bridge returned an invalid update check payload.');
  }

  return {
    state: value.state === 'unconfigured' || value.state === 'update_available' || value.state === 'up_to_date'
      ? value.state
      : 'unsupported',
    current_version: typeof value.current_version === 'string' ? value.current_version : null,
    release_environment: typeof value.release_environment === 'string' ? value.release_environment : null,
    updater_endpoint: typeof value.updater_endpoint === 'string' ? value.updater_endpoint : null,
    update_version: typeof value.update_version === 'string' ? value.update_version : null,
    notes: typeof value.notes === 'string' ? value.notes : null,
    pub_date: typeof value.pub_date === 'string' ? value.pub_date : null,
    error: typeof value.error === 'string' ? value.error : null,
  };
}

function toInstallResult(value: unknown): StoreRuntimeUpdateInstallResult {
  if (!isObject(value)) {
    throw new Error('Native runtime updater bridge returned an invalid update install payload.');
  }

  return {
    state: value.state === 'unconfigured' || value.state === 'installed' || value.state === 'up_to_date'
      ? value.state
      : 'unsupported',
    current_version: typeof value.current_version === 'string' ? value.current_version : null,
    release_environment: typeof value.release_environment === 'string' ? value.release_environment : null,
    updater_endpoint: typeof value.updater_endpoint === 'string' ? value.updater_endpoint : null,
    installed_version: typeof value.installed_version === 'string' ? value.installed_version : null,
    error: typeof value.error === 'string' ? value.error : null,
  };
}

export function createResolvedStoreRuntimeUpdater(options: {
  invoke?: Invoke;
  isNativeRuntime?: () => boolean;
} = {}): StoreRuntimeUpdaterAdapter {
  const invoke = options.invoke ?? tauriInvoke;
  const isNativeRuntime = options.isNativeRuntime ?? isNativeStoreRuntimeShellAvailable;

  if (!isNativeRuntime()) {
    return {
      async check() {
        return {
          state: 'unsupported',
          current_version: null,
          release_environment: null,
          updater_endpoint: null,
          update_version: null,
          notes: null,
          pub_date: null,
          error: 'Updater checks are only available in the packaged desktop runtime.',
        };
      },
      async install() {
        return {
          state: 'unsupported',
          current_version: null,
          release_environment: null,
          updater_endpoint: null,
          installed_version: null,
          error: 'Updater installation is only available in the packaged desktop runtime.',
        };
      },
    };
  }

  return {
    async check() {
      return toCheckResult(await invoke('cmd_check_store_runtime_update'));
    },
    async install() {
      return toInstallResult(await invoke('cmd_install_store_runtime_update'));
    },
  };
}
