import type {
  ControlPlaneActor,
  ControlPlaneInvite,
  ControlPlanePlatformTenantRecord,
  ControlPlaneSession,
  ControlPlaneTenant,
} from '@store/types';

async function request<T>(path: string, init?: RequestInit, accessToken?: string): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      'content-type': 'application/json',
      ...(accessToken ? { authorization: `Bearer ${accessToken}` } : {}),
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw new Error(`Control-plane request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export const platformAdminClient = {
  exchangeSession(token: string) {
    return request<ControlPlaneSession>('/v1/auth/oidc/exchange', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  },
  getActor(accessToken: string) {
    return request<ControlPlaneActor>('/v1/auth/me', undefined, accessToken);
  },
  listTenants(accessToken: string) {
    return request<{ records: ControlPlanePlatformTenantRecord[] }>('/v1/platform/tenants', undefined, accessToken);
  },
  createTenant(accessToken: string, payload: { name: string; slug: string }) {
    return request<ControlPlaneTenant>(
      '/v1/platform/tenants',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
  createOwnerInvite(accessToken: string, tenantId: string, payload: { email: string; full_name: string }) {
    return request<ControlPlaneInvite>(
      `/v1/platform/tenants/${tenantId}/owner-invites`,
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
  },
};
