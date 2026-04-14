import { startTransition, useState } from 'react';
import type {
  ControlPlaneActor,
  ControlPlaneBillingPlan,
  ControlPlaneInvite,
  ControlPlanePlatformTenantRecord,
  ControlPlaneTenantLifecycleSummary,
} from '@store/types';
import { platformAdminClient } from './client';

export function usePlatformAdminWorkspace() {
  const [korsenexToken, setKorsenexToken] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [actor, setActor] = useState<ControlPlaneActor | null>(null);
  const [tenants, setTenants] = useState<ControlPlanePlatformTenantRecord[]>([]);
  const [billingPlans, setBillingPlans] = useState<ControlPlaneBillingPlan[]>([]);
  const [activeTenantLifecycle, setActiveTenantLifecycle] = useState<ControlPlaneTenantLifecycleSummary | null>(null);
  const [activeTenantId, setActiveTenantId] = useState('');
  const [tenantName, setTenantName] = useState('');
  const [tenantSlug, setTenantSlug] = useState('');
  const [planCode, setPlanCode] = useState('');
  const [planName, setPlanName] = useState('');
  const [planAmountMinor, setPlanAmountMinor] = useState('');
  const [planBranchLimit, setPlanBranchLimit] = useState('');
  const [planDeviceLimit, setPlanDeviceLimit] = useState('');
  const [ownerEmail, setOwnerEmail] = useState('');
  const [ownerFullName, setOwnerFullName] = useState('');
  const [latestInvite, setLatestInvite] = useState<ControlPlaneInvite | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);

  async function loadTenantLifecycle(nextAccessToken: string, tenantId: string) {
    if (!tenantId) {
      setActiveTenantLifecycle(null);
      return;
    }
    const lifecycle = await platformAdminClient.getTenantBillingLifecycle(nextAccessToken, tenantId);
    startTransition(() => {
      setActiveTenantLifecycle(lifecycle);
    });
  }

  async function selectTenant(tenantId: string) {
    startTransition(() => {
      setActiveTenantId(tenantId);
    });
    if (!accessToken || !tenantId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      await loadTenantLifecycle(accessToken, tenantId);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load tenant lifecycle');
    } finally {
      setIsBusy(false);
    }
  }

  async function startSession() {
    setIsBusy(true);
    setErrorMessage('');
    try {
      const session = await platformAdminClient.exchangeSession(korsenexToken);
      const [nextActor, tenantList, planList] = await Promise.all([
        platformAdminClient.getActor(session.access_token),
        platformAdminClient.listTenants(session.access_token),
        platformAdminClient.listBillingPlans(session.access_token),
      ]);
      const selectedTenantId = tenantList.records[0]?.tenant_id ?? '';
      const lifecycle = selectedTenantId
        ? await platformAdminClient.getTenantBillingLifecycle(session.access_token, selectedTenantId)
        : null;
      startTransition(() => {
        setAccessToken(session.access_token);
        setActor(nextActor);
        setTenants(tenantList.records);
        setBillingPlans(planList.records);
        setActiveTenantId(selectedTenantId);
        setActiveTenantLifecycle(lifecycle);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to start session');
    } finally {
      setIsBusy(false);
    }
  }

  async function createTenant() {
    if (!accessToken) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const createdTenant = await platformAdminClient.createTenant(accessToken, {
        name: tenantName,
        slug: tenantSlug,
      });
      const [tenantList, lifecycle] = await Promise.all([
        platformAdminClient.listTenants(accessToken),
        platformAdminClient.getTenantBillingLifecycle(accessToken, createdTenant.id),
      ]);
      startTransition(() => {
        setTenants(tenantList.records);
        setActiveTenantId(createdTenant.id);
        setActiveTenantLifecycle(lifecycle);
        setTenantName('');
        setTenantSlug('');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to create tenant');
    } finally {
      setIsBusy(false);
    }
  }

  async function sendOwnerInvite() {
    if (!accessToken || !activeTenantId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const invite = await platformAdminClient.createOwnerInvite(accessToken, activeTenantId, {
        email: ownerEmail,
        full_name: ownerFullName,
      });
      startTransition(() => {
        setLatestInvite(invite);
        setOwnerEmail('');
        setOwnerFullName('');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to send owner invite');
    } finally {
      setIsBusy(false);
    }
  }

  async function createBillingPlan() {
    if (!accessToken) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      await platformAdminClient.createBillingPlan(accessToken, {
        code: planCode,
        display_name: planName,
        billing_cadence: 'monthly',
        currency_code: 'INR',
        amount_minor: Number(planAmountMinor),
        trial_days: 14,
        branch_limit: Number(planBranchLimit),
        device_limit: Number(planDeviceLimit),
        offline_runtime_hours: 48,
        grace_window_days: 5,
        feature_flags: { offline_continuity: true },
        provider_plan_refs: {
          cashfree: `cf_plan_${planCode.replace(/-/g, '_')}`,
          razorpay: `rp_plan_${planCode.replace(/-/g, '_')}`,
        },
        is_default: false,
      });
      const refreshedPlans = await platformAdminClient.listBillingPlans(accessToken);
      startTransition(() => {
        setBillingPlans(refreshedPlans.records);
        setPlanCode('');
        setPlanName('');
        setPlanAmountMinor('');
        setPlanBranchLimit('');
        setPlanDeviceLimit('');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to create billing plan');
    } finally {
      setIsBusy(false);
    }
  }

  async function suspendActiveTenantAccess() {
    if (!accessToken || !activeTenantId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const lifecycle = await platformAdminClient.suspendTenantAccess(accessToken, activeTenantId, 'Billing review hold');
      startTransition(() => {
        setActiveTenantLifecycle(lifecycle);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to suspend tenant access');
    } finally {
      setIsBusy(false);
    }
  }

  async function reactivateActiveTenantAccess() {
    if (!accessToken || !activeTenantId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const lifecycle = await platformAdminClient.reactivateTenantAccess(accessToken, activeTenantId);
      startTransition(() => {
        setActiveTenantLifecycle(lifecycle);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to reactivate tenant access');
    } finally {
      setIsBusy(false);
    }
  }

  return {
    actor,
    activeTenantLifecycle,
    activeTenantId,
    billingPlans,
    errorMessage,
    isBusy,
    korsenexToken,
    latestInvite,
    ownerEmail,
    ownerFullName,
    planAmountMinor,
    planBranchLimit,
    planCode,
    planDeviceLimit,
    planName,
    tenantName,
    tenantSlug,
    tenants,
    createBillingPlan,
    reactivateActiveTenantAccess,
    selectTenant,
    setKorsenexToken,
    setOwnerEmail,
    setOwnerFullName,
    setPlanAmountMinor,
    setPlanBranchLimit,
    setPlanCode,
    setPlanDeviceLimit,
    setPlanName,
    setTenantName,
    setTenantSlug,
    createTenant,
    sendOwnerInvite,
    startSession,
    suspendActiveTenantAccess,
  };
}
