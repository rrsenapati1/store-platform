import {
  createResolvedStoreRuntimeShell,
  DEFAULT_PACKAGED_CONTROL_PLANE_BASE_URL,
  type StoreRuntimeShellStatus,
} from '../runtime-shell/storeRuntimeShell';

function normalizeBaseUrl(value: string | null | undefined): string | null {
  const normalized = `${value ?? ''}`.trim().replace(/\/+$/, '');
  return normalized ? normalized : null;
}

function normalizePath(path: string): string {
  const trimmed = path.trim();
  if (!trimmed) {
    return '/';
  }
  return trimmed.startsWith('/') ? trimmed : `/${trimmed}`;
}

export function resolveControlPlaneUrl(path: string, shellStatus: StoreRuntimeShellStatus | null): string {
  const normalizedPath = normalizePath(path);
  const baseUrl = normalizeBaseUrl(shellStatus?.control_plane_base_url);
  if (!baseUrl) {
    return normalizedPath;
  }

  const browserOrigin = typeof window !== 'undefined' ? normalizeBaseUrl(window.location.origin) : null;
  if (shellStatus?.runtime_kind === 'browser_web' && browserOrigin === baseUrl) {
    return normalizedPath;
  }

  return new URL(normalizedPath, `${baseUrl}/`).toString();
}

export async function resolveControlPlaneRequestUrl(path: string): Promise<string> {
  try {
    const shellStatus = await createResolvedStoreRuntimeShell().getStatus();
    const normalizedShellStatus = shellStatus.runtime_kind === 'packaged_desktop'
      ? {
          ...shellStatus,
          control_plane_base_url: normalizeBaseUrl(shellStatus.control_plane_base_url) ?? DEFAULT_PACKAGED_CONTROL_PLANE_BASE_URL,
        }
      : shellStatus;
    return resolveControlPlaneUrl(path, normalizedShellStatus);
  } catch {
    return normalizePath(path);
  }
}
