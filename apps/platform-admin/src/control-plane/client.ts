import type {
  ControlPlaneActor,
  ControlPlaneBillingPlan,
  ControlPlaneInvite,
  ControlPlaneTenantLifecycleSummary,
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
  listBillingPlans(accessToken: string) {
    return request<{ records: ControlPlaneBillingPlan[] }>('/v1/platform/billing/plans', undefined, accessToken);
  },
  createBillingPlan(
    accessToken: string,
    payload: {
      code: string;
      display_name: string;
      billing_cadence: string;
      currency_code: string;
      amount_minor: number;
      trial_days: number;
      branch_limit: number;
      device_limit: number;
      offline_runtime_hours: number;
      grace_window_days: number;
      feature_flags: Record<string, unknown>;
      provider_plan_refs: Record<string, string>;
      is_default: boolean;
    },
  ) {
    return request<ControlPlaneBillingPlan>(
      '/v1/platform/billing/plans',
      {
        method: 'POST',
        body: JSON.stringify(payload),
      },
      accessToken,
    );
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
  getTenantBillingLifecycle(accessToken: string, tenantId: string) {
    return request<ControlPlaneTenantLifecycleSummary>(
      `/v1/platform/tenants/${tenantId}/billing-lifecycle`,
      undefined,
      accessToken,
    );
  },
  suspendTenantAccess(accessToken: string, tenantId: string, reason: string) {
    return request<ControlPlaneTenantLifecycleSummary>(
      `/v1/platform/tenants/${tenantId}/billing/suspend`,
      {
        method: 'POST',
        body: JSON.stringify({ reason }),
      },
      accessToken,
    );
  },
  reactivateTenantAccess(accessToken: string, tenantId: string) {
    return request<ControlPlaneTenantLifecycleSummary>(
      `/v1/platform/tenants/${tenantId}/billing/reactivate`,
      {
        method: 'POST',
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
