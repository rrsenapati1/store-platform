import { startTransition, useEffect, useRef, useState } from 'react';
import {
  buildKorsenexSignInUrl,
  clearStoreWebSession,
  consumeLocalDevBootstrapFromWindow,
  exchangeStoreWebSession,
  isStoreWebSessionExpired,
  loadStoreWebSession,
  readKorsenexCallback,
  refreshStoreWebSession,
  shouldRefreshStoreWebSession,
  signOutStoreWebSession,
} from '@store/auth';
import type {
  ControlPlaneActor,
  ControlPlaneBillingPlan,
  ControlPlaneInvite,
  ControlPlaneObservabilitySummary,
  ControlPlanePlatformTenantRecord,
  ControlPlaneSystemEnvironmentContract,
  ControlPlaneSystemSecurityControls,
  ControlPlaneTenantLifecycleSummary,
} from '@store/types';
import { platformAdminClient } from './client';
import {
  buildPlatformAdminOverviewModel,
  type PlatformAdminSection,
} from './platformAdminOverviewModel';
import type { PlatformAdminSessionState } from './PlatformAdminAuthEntrySurface';

const PLATFORM_ADMIN_SESSION_STORAGE_KEY = 'platform-admin.session';

export function usePlatformAdminWorkspace() {
  const [korsenexToken, setKorsenexToken] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [sessionExpiresAt, setSessionExpiresAt] = useState<string | null>(null);
  const [sessionState, setSessionState] = useState<PlatformAdminSessionState>('restoring');
  const [actor, setActor] = useState<ControlPlaneActor | null>(null);
  const [tenants, setTenants] = useState<ControlPlanePlatformTenantRecord[]>([]);
  const [billingPlans, setBillingPlans] = useState<ControlPlaneBillingPlan[]>([]);
  const [activeTenantLifecycle, setActiveTenantLifecycle] = useState<ControlPlaneTenantLifecycleSummary | null>(null);
  const [observabilitySummary, setObservabilitySummary] = useState<ControlPlaneObservabilitySummary | null>(null);
  const [securityControls, setSecurityControls] = useState<ControlPlaneSystemSecurityControls | null>(null);
  const [environmentContract, setEnvironmentContract] = useState<ControlPlaneSystemEnvironmentContract | null>(null);
  const [activeTenantId, setActiveTenantId] = useState('');
  const [activeSection, setActiveSection] = useState<PlatformAdminSection>('overview');
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
  const hasBootstrappedSessionRef = useRef(false);

  async function loadPlatformSessionData(nextAccessToken: string) {
    const [nextActor, tenantList, planList, summary, nextSecurityControls, nextEnvironmentContract] = await Promise.all([
      platformAdminClient.getActor(nextAccessToken),
      platformAdminClient.listTenants(nextAccessToken),
      platformAdminClient.listBillingPlans(nextAccessToken),
      platformAdminClient.getObservabilitySummary(nextAccessToken),
      platformAdminClient.getSecurityControls(nextAccessToken),
      platformAdminClient.getEnvironmentContract(nextAccessToken),
    ]);
    const selectedTenantId = tenantList.records[0]?.tenant_id ?? '';
    const lifecycle = selectedTenantId
      ? await platformAdminClient.getTenantBillingLifecycle(nextAccessToken, selectedTenantId)
      : null;
    return {
      actor: nextActor,
      billingPlans: planList.records,
      environmentContract: nextEnvironmentContract,
      lifecycle,
      observabilitySummary: summary,
      securityControls: nextSecurityControls,
      selectedTenantId,
      tenants: tenantList.records,
    };
  }

  function resetSessionState() {
    startTransition(() => {
      setAccessToken('');
      setSessionExpiresAt(null);
      setSessionState('signed_out');
      setActor(null);
      setTenants([]);
      setBillingPlans([]);
      setActiveTenantLifecycle(null);
      setObservabilitySummary(null);
      setSecurityControls(null);
      setEnvironmentContract(null);
      setActiveTenantId('');
      setActiveSection('overview');
      setLatestInvite(null);
    });
  }

  function applySessionData(input: {
    accessToken: string;
    expiresAt: string;
  } & Awaited<ReturnType<typeof loadPlatformSessionData>>) {
    startTransition(() => {
      setAccessToken(input.accessToken);
      setSessionExpiresAt(input.expiresAt);
      setSessionState('ready');
      setActor(input.actor);
      setTenants(input.tenants);
      setBillingPlans(input.billingPlans);
      setObservabilitySummary(input.observabilitySummary);
      setSecurityControls(input.securityControls);
      setEnvironmentContract(input.environmentContract);
      setActiveTenantId(input.selectedTenantId);
      setActiveTenantLifecycle(input.lifecycle);
      setActiveSection('overview');
    });
  }

  function resolveSessionFailureMessage(error: unknown, fallback: string) {
    return error instanceof Error ? error.message : fallback;
  }

  function handleSessionFailure(nextState: Exclude<PlatformAdminSessionState, 'ready' | 'restoring'>, fallback: string, error: unknown) {
    clearStoreWebSession(PLATFORM_ADMIN_SESSION_STORAGE_KEY);
    resetSessionState();
    setErrorMessage(resolveSessionFailureMessage(error, fallback));
    setSessionState(nextState);
  }

  async function hydratePlatformSession(record: { accessToken: string; expiresAt: string }) {
    const sessionData = await loadPlatformSessionData(record.accessToken);
    applySessionData({
      accessToken: record.accessToken,
      actor: sessionData.actor,
      billingPlans: sessionData.billingPlans,
      environmentContract: sessionData.environmentContract,
      expiresAt: record.expiresAt,
      lifecycle: sessionData.lifecycle,
      observabilitySummary: sessionData.observabilitySummary,
      securityControls: sessionData.securityControls,
      selectedTenantId: sessionData.selectedTenantId,
      tenants: sessionData.tenants,
    });
  }

  async function exchangePlatformSessionToken(token: string, options?: { manageBusy?: boolean }) {
    const manageBusy = options?.manageBusy ?? true;
    if (manageBusy) {
      setIsBusy(true);
    }
    setErrorMessage('');
    setSessionState('restoring');
    try {
      const record = await exchangeStoreWebSession({
        token,
        exchange: platformAdminClient.exchangeSession,
        storageKey: PLATFORM_ADMIN_SESSION_STORAGE_KEY,
      });
      await hydratePlatformSession(record);
    } catch (error) {
      handleSessionFailure('revoked', 'Unable to start session', error);
    } finally {
      if (manageBusy) {
        setIsBusy(false);
      }
    }
  }

  async function refreshPlatformSession(recordOverride?: { accessToken: string; expiresAt: string }) {
    const currentRecord = recordOverride ?? (accessToken && sessionExpiresAt ? { accessToken, expiresAt: sessionExpiresAt } : null);
    if (!currentRecord) {
      return;
    }
    try {
      const refreshed = await refreshStoreWebSession({
        record: currentRecord,
        refresh: platformAdminClient.refreshSession,
        storageKey: PLATFORM_ADMIN_SESSION_STORAGE_KEY,
      });
      await hydratePlatformSession(refreshed);
    } catch (error) {
      handleSessionFailure('expired', 'Unable to refresh platform session', error);
    }
  }

  async function restoreSession() {
    if (typeof window === 'undefined') {
      setSessionState('signed_out');
      return;
    }
    setErrorMessage('');
    setSessionState('restoring');

    const callback = readKorsenexCallback(window);
    if (callback.error) {
      handleSessionFailure('revoked', 'Unable to complete platform sign-in', new Error(callback.error));
      return;
    }
    if (callback.token) {
      await exchangePlatformSessionToken(callback.token, { manageBusy: false });
      return;
    }

    if (import.meta.env.DEV) {
      const bootstrap = consumeLocalDevBootstrapFromWindow(window);
      if (bootstrap.korsenexToken) {
        setKorsenexToken(bootstrap.korsenexToken);
        if (bootstrap.autoStart) {
          await exchangePlatformSessionToken(bootstrap.korsenexToken, { manageBusy: false });
          return;
        }
      }
    }

    const storedSession = loadStoreWebSession(PLATFORM_ADMIN_SESSION_STORAGE_KEY);
    if (!storedSession) {
      setSessionState('signed_out');
      return;
    }

    try {
      if (isStoreWebSessionExpired(storedSession) || shouldRefreshStoreWebSession(storedSession)) {
        await refreshPlatformSession(storedSession);
        return;
      }
      await hydratePlatformSession(storedSession);
    } catch (error) {
      handleSessionFailure('expired', 'Unable to restore platform session', error);
    }
  }

  useEffect(() => {
    if (hasBootstrappedSessionRef.current) {
      return;
    }
    hasBootstrappedSessionRef.current = true;
    void restoreSession();
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined' || !accessToken || !sessionExpiresAt || sessionState !== 'ready') {
      return;
    }
    const refreshDelayMs = Math.max(Date.parse(sessionExpiresAt) - Date.now() - 120_000, 1_000);
    const timer = window.setTimeout(() => {
      void refreshPlatformSession();
    }, refreshDelayMs);
    return () => {
      window.clearTimeout(timer);
    };
  }, [accessToken, sessionExpiresAt, sessionState]);

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

  async function refreshObservabilitySummary(nextAccessToken = accessToken) {
    if (!nextAccessToken) {
      setObservabilitySummary(null);
      return;
    }
    const summary = await platformAdminClient.getObservabilitySummary(nextAccessToken);
    startTransition(() => {
      setObservabilitySummary(summary);
    });
  }

  async function refreshPlatformPosture(nextAccessToken = accessToken) {
    if (!nextAccessToken) {
      setObservabilitySummary(null);
      setSecurityControls(null);
      setEnvironmentContract(null);
      return;
    }
    const [summary, nextSecurityControls, nextEnvironmentContract] = await Promise.all([
      platformAdminClient.getObservabilitySummary(nextAccessToken),
      platformAdminClient.getSecurityControls(nextAccessToken),
      platformAdminClient.getEnvironmentContract(nextAccessToken),
    ]);
    startTransition(() => {
      setObservabilitySummary(summary);
      setSecurityControls(nextSecurityControls);
      setEnvironmentContract(nextEnvironmentContract);
    });
  }

  async function startSession() {
    if (!korsenexToken) {
      return;
    }
    await exchangePlatformSessionToken(korsenexToken);
  }

  function beginSignIn() {
    if (typeof window === 'undefined') {
      return;
    }
    const authorizeBaseUrl = import.meta.env.VITE_KORSENEX_AUTHORIZE_URL;
    if (!authorizeBaseUrl) {
      setErrorMessage('VITE_KORSENEX_AUTHORIZE_URL is not configured');
      setSessionState('signed_out');
      return;
    }
    const nextUrl = buildKorsenexSignInUrl({
      authorizeBaseUrl,
      returnTo: window.location.href,
      state: 'platform-admin',
    });
    window.location.assign(nextUrl);
  }

  async function signOut() {
    const currentRecord = accessToken && sessionExpiresAt ? { accessToken, expiresAt: sessionExpiresAt } : null;
    setIsBusy(true);
    setErrorMessage('');
    try {
      if (currentRecord) {
        await signOutStoreWebSession({
          accessToken: currentRecord.accessToken,
          signOut: async (sessionAccessToken) => {
            await platformAdminClient.signOut(sessionAccessToken);
          },
          storageKey: PLATFORM_ADMIN_SESSION_STORAGE_KEY,
        });
      } else {
        clearStoreWebSession(PLATFORM_ADMIN_SESSION_STORAGE_KEY);
      }
      resetSessionState();
    } catch (error) {
      setErrorMessage(resolveSessionFailureMessage(error, 'Unable to sign out'));
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

  const overviewModel = buildPlatformAdminOverviewModel({
    observabilitySummary,
    securityControls,
    environmentContract,
    tenants,
    activeTenantLifecycle,
  });

  return {
    actor,
    activeSection,
    activeTenantLifecycle,
    activeTenantId,
    billingPlans,
    beginSignIn,
    environmentContract,
    errorMessage,
    isBusy,
    korsenexToken,
    latestInvite,
    observabilitySummary,
    overviewModel,
    ownerEmail,
    ownerFullName,
    planAmountMinor,
    planBranchLimit,
    planCode,
    planDeviceLimit,
    planName,
    securityControls,
    tenantName,
    tenantSlug,
    tenants,
    createBillingPlan,
    reactivateActiveTenantAccess,
    refreshObservabilitySummary,
    refreshPlatformPosture,
    selectTenant,
    setActiveSection,
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
    sessionState,
    signOut,
    startSession,
    suspendActiveTenantAccess,
  };
}
