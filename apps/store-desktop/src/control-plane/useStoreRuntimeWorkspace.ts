import { startTransition, useEffect, useRef, useState } from 'react';
import type {
  ControlPlaneActor,
  ControlPlaneBatchExpiryReport,
  ControlPlaneBatchExpiryWriteOff,
  ControlPlaneBarcodeScanLookup,
  ControlPlaneBranchCatalogItem,
  ControlPlaneExchange,
  ControlPlaneBranchRecord,
  ControlPlaneDeviceRecord,
  ControlPlaneInventorySnapshotRecord,
  ControlPlanePrintJob,
  ControlPlaneRuntimeDeviceClaimResolution,
  ControlPlaneRuntimeHeartbeat,
  ControlPlaneSale,
  ControlPlaneSaleRecord,
  ControlPlaneSaleReturn,
  ControlPlaneStoreDesktopActivationSession,
  ControlPlaneTenant,
} from '@store/types';
import {
  createResolvedStoreRuntimeCache,
  type StoreRuntimeCachePersistence,
  type StoreRuntimeCacheSnapshot,
  type StoreRuntimePendingMutation,
} from '../runtime-cache/storeRuntimeCache';
import { resolveStoreRuntimeDeviceBinding } from './runtimeDeviceBinding';
import {
  createPendingCreditNotePrintMutation,
  createPendingHeartbeatMutation,
  createPendingSalesInvoicePrintMutation,
  replayPendingRuntimeMutations,
  shouldQueueRuntimeOutboxMutation,
} from './runtimeOutbox';
import {
  clearStoreRuntimeSession,
  isStoreRuntimeSessionExpired,
  loadStoreRuntimeSession,
  saveStoreRuntimeSession,
  type StoreRuntimeSessionRecord,
} from './storeRuntimeSessionStore';
import { resolveStoreRuntimeSessionRestorePolicy } from './storeRuntimeSessionRestorePolicy';
import {
  clearStoreRuntimeLocalAuth,
  isStoreRuntimeLocalAuthOfflineExpired,
  loadStoreRuntimeLocalAuth,
  saveStoreRuntimeLocalAuth,
  type StoreRuntimeLocalAuthRecord,
  STORE_RUNTIME_LOCAL_AUTH_SCHEMA_VERSION,
} from './storeRuntimeLocalAuthStore';
import {
  loadStoreRuntimeHubIdentity,
  type StoreRuntimeHubIdentityRecord,
} from './storeRuntimeHubIdentityStore';
import {
  createStoreRuntimePinSalt,
  hashStoreRuntimePin,
  isStoreRuntimePinFormatValid,
  isStoreRuntimePinLocked,
  recordFailedStoreRuntimePinAttempt,
  recordSuccessfulStoreRuntimePinUnlock,
  STORE_RUNTIME_PIN_ATTEMPT_LIMIT,
  STORE_RUNTIME_PIN_LOCKOUT_SECONDS,
  verifyStoreRuntimePin,
} from './storeRuntimePinAuth';
import { isStoreRuntimeDeveloperBootstrapEnabled } from './storeRuntimeAuthMode';
import { ensureStoreRuntimeHubIdentity } from './runtimeHubIdentity';
import { loadStoreRuntimeShellStatus, useStoreRuntimeShellStatus } from './useStoreRuntimeShellStatus';
import { ControlPlaneRequestError, storeControlPlaneClient } from './client';
type CacheStatus = 'EMPTY' | 'HYDRATED' | 'SYNCED';

export function useStoreRuntimeWorkspace() {
  const {
    runtimeShellError,
    runtimeShellStatus,
  } = useStoreRuntimeShellStatus();
  const [activationCode, setActivationCode] = useState('');
  const [pendingPinEnrollmentSession, setPendingPinEnrollmentSession] = useState<ControlPlaneStoreDesktopActivationSession | null>(null);
  const [newPin, setNewPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [unlockPin, setUnlockPin] = useState('');
  const [korsenexToken, setKorsenexToken] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [sessionExpiresAt, setSessionExpiresAt] = useState<string | null>(null);
  const [hasLoadedLocalAuth, setHasLoadedLocalAuth] = useState(false);
  const [localAuthRecord, setLocalAuthRecord] = useState<StoreRuntimeLocalAuthRecord | null>(null);
  const [hubIdentityRecord, setHubIdentityRecord] = useState<StoreRuntimeHubIdentityRecord | null>(null);
  const [isLocalUnlocked, setIsLocalUnlocked] = useState(false);
  const [actor, setActor] = useState<ControlPlaneActor | null>(null);
  const [tenant, setTenant] = useState<ControlPlaneTenant | null>(null);
  const [branches, setBranches] = useState<ControlPlaneBranchRecord[]>([]);
  const [branchCatalogItems, setBranchCatalogItems] = useState<ControlPlaneBranchCatalogItem[]>([]);
  const [batchExpiryReport, setBatchExpiryReport] = useState<ControlPlaneBatchExpiryReport | null>(null);
  const [inventorySnapshot, setInventorySnapshot] = useState<ControlPlaneInventorySnapshotRecord[]>([]);
  const [sales, setSales] = useState<ControlPlaneSaleRecord[]>([]);
  const [runtimeDevices, setRuntimeDevices] = useState<ControlPlaneDeviceRecord[]>([]);
  const [selectedRuntimeDeviceId, setSelectedRuntimeDeviceId] = useState('');
  const [runtimeDeviceClaim, setRuntimeDeviceClaim] = useState<ControlPlaneRuntimeDeviceClaimResolution | null>(null);
  const [runtimeHeartbeat, setRuntimeHeartbeat] = useState<ControlPlaneRuntimeHeartbeat | null>(null);
  const [printJobs, setPrintJobs] = useState<ControlPlanePrintJob[]>([]);
  const [latestPrintJob, setLatestPrintJob] = useState<ControlPlanePrintJob | null>(null);
  const [latestBatchWriteOff, setLatestBatchWriteOff] = useState<ControlPlaneBatchExpiryWriteOff | null>(null);
  const [latestScanLookup, setLatestScanLookup] = useState<ControlPlaneBarcodeScanLookup | null>(null);
  const [latestSale, setLatestSale] = useState<ControlPlaneSale | null>(null);
  const [latestSaleReturn, setLatestSaleReturn] = useState<ControlPlaneSaleReturn | null>(null);
  const [latestExchange, setLatestExchange] = useState<ControlPlaneExchange | null>(null);
  const [cacheStatus, setCacheStatus] = useState<CacheStatus>('EMPTY');
  const [cachePersistence, setCachePersistence] = useState<StoreRuntimeCachePersistence>({
    backend_kind: 'unavailable',
    backend_label: 'Runtime cache unavailable',
    cached_at: null,
    detail: null,
    location: null,
    snapshot_present: false,
  });
  const [lastCachedAt, setLastCachedAt] = useState<string | null>(null);
  const [pendingMutations, setPendingMutations] = useState<StoreRuntimePendingMutation[]>([]);
  const [pendingMutationCount, setPendingMutationCount] = useState(0);
  const [customerName, setCustomerName] = useState('');
  const [customerGstin, setCustomerGstin] = useState('');
  const [saleQuantity, setSaleQuantity] = useState('1');
  const [scannedBarcode, setScannedBarcode] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('Cash');
  const [returnQuantity, setReturnQuantity] = useState('1');
  const [refundAmount, setRefundAmount] = useState('');
  const [refundMethod, setRefundMethod] = useState('Cash');
  const [exchangeReturnQuantity, setExchangeReturnQuantity] = useState('1');
  const [replacementQuantity, setReplacementQuantity] = useState('1');
  const [exchangeSettlementMethod, setExchangeSettlementMethod] = useState('Cash');
  const [expiryWriteOffQuantity, setExpiryWriteOffQuantity] = useState('1');
  const [expiryWriteOffReason, setExpiryWriteOffReason] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isBusy, setIsBusy] = useState(false);
  const sessionRecordRef = useRef<StoreRuntimeSessionRecord | null>(null);
  const isSessionLive = Boolean(accessToken);
  const supportsDeveloperSessionBootstrap = runtimeShellStatus?.runtime_kind !== 'packaged_desktop'
    && isStoreRuntimeDeveloperBootstrapEnabled();
  const requiresPinEnrollment = pendingPinEnrollmentSession !== null;
  const requiresLocalUnlock = runtimeShellStatus?.runtime_kind === 'packaged_desktop'
    && hasLoadedLocalAuth
    && localAuthRecord !== null
    && !isLocalUnlocked
    && !requiresPinEnrollment;

  const tenantId = actor?.tenant_memberships[0]?.tenant_id ?? actor?.branch_memberships[0]?.tenant_id ?? '';
  const branchId = actor?.branch_memberships[0]?.branch_id ?? branches[0]?.branch_id ?? '';

  function queuePendingMutation(mutation: StoreRuntimePendingMutation, message: string) {
    startTransition(() => {
      setPendingMutations((current) => {
        const next = [...current, mutation];
        setPendingMutationCount(next.length);
        return next;
      });
      setErrorMessage(message);
    });
  }

  function resetRuntimeWorkspaceState() {
    sessionRecordRef.current = null;
    startTransition(() => {
      setPendingPinEnrollmentSession(null);
      setNewPin('');
      setConfirmPin('');
      setUnlockPin('');
      setIsLocalUnlocked(false);
      setAccessToken('');
      setSessionExpiresAt(null);
      setActor(null);
      setTenant(null);
      setBranches([]);
      setBranchCatalogItems([]);
      setBatchExpiryReport(null);
      setInventorySnapshot([]);
      setSales([]);
      setRuntimeDevices([]);
      setSelectedRuntimeDeviceId('');
      setRuntimeDeviceClaim(null);
      setRuntimeHeartbeat(null);
      setPrintJobs([]);
      setLatestPrintJob(null);
      setLatestBatchWriteOff(null);
      setLatestScanLookup(null);
      setLatestSale(null);
      setLatestSaleReturn(null);
      setLatestExchange(null);
      setPendingMutations([]);
      setPendingMutationCount(0);
      setCacheStatus('EMPTY');
      setLastCachedAt(null);
      setErrorMessage('');
    });
  }

  function applyCachedRuntimeSnapshot(cachedSnapshot: StoreRuntimeCacheSnapshot) {
    startTransition(() => {
      setActor(cachedSnapshot.actor);
      setTenant(cachedSnapshot.tenant);
      setBranches(cachedSnapshot.branches);
      setBranchCatalogItems(cachedSnapshot.branch_catalog_items);
      setInventorySnapshot(cachedSnapshot.inventory_snapshot);
      setSales(cachedSnapshot.sales);
      setRuntimeDevices(cachedSnapshot.runtime_devices);
      setSelectedRuntimeDeviceId(cachedSnapshot.selected_runtime_device_id || (cachedSnapshot.runtime_devices[0]?.id ?? ''));
      setRuntimeHeartbeat(cachedSnapshot.runtime_heartbeat);
      setPrintJobs(cachedSnapshot.print_jobs);
      setLatestPrintJob(cachedSnapshot.latest_print_job);
      setLatestSale(cachedSnapshot.latest_sale);
      setLatestSaleReturn(cachedSnapshot.latest_sale_return);
      setLatestExchange(cachedSnapshot.latest_exchange);
      setPendingMutations(cachedSnapshot.pending_mutations);
      setCacheStatus('HYDRATED');
      setLastCachedAt(cachedSnapshot.cached_at);
      setPendingMutationCount(cachedSnapshot.pending_mutations.length);
    });
  }

  async function bootstrapRuntimeSession(nextSession: StoreRuntimeSessionRecord) {
    const nextActor = await storeControlPlaneClient.getActor(nextSession.access_token);
    const nextTenantId = nextActor.tenant_memberships[0]?.tenant_id ?? nextActor.branch_memberships[0]?.tenant_id;
    if (!nextTenantId) {
      throw new Error('Runtime session is not bound to a tenant');
    }
    const tenantSummary = await storeControlPlaneClient.getTenantSummary(nextSession.access_token, nextTenantId);
    const branchList = await storeControlPlaneClient.listBranches(nextSession.access_token, nextTenantId);
    const activeBranchId = nextActor.branch_memberships[0]?.branch_id ?? branchList.records[0]?.branch_id;
    const resolvedRuntimeShellStatus = await loadStoreRuntimeShellStatus().catch(() => runtimeShellStatus);
    const [catalogResponse, snapshotResponse, salesResponse, devicesResponse] = activeBranchId
      ? await Promise.all([
          storeControlPlaneClient.listBranchCatalogItems(nextSession.access_token, nextTenantId, activeBranchId),
          storeControlPlaneClient.listInventorySnapshot(nextSession.access_token, nextTenantId, activeBranchId),
          storeControlPlaneClient.listSales(nextSession.access_token, nextTenantId, activeBranchId),
          storeControlPlaneClient.listRuntimeDevices(nextSession.access_token, nextTenantId, activeBranchId),
        ])
      : [{ records: [] }, { records: [] }, { records: [] }, { records: [] }];
    const runtimeDeviceBinding = activeBranchId
      ? await resolveStoreRuntimeDeviceBinding({
          accessToken: nextSession.access_token,
          tenantId: nextTenantId,
          branchId: activeBranchId,
          runtimeDevices: devicesResponse.records,
          runtimeShellStatus: resolvedRuntimeShellStatus,
        })
      : { selectedRuntimeDeviceId: '', runtimeDeviceClaim: null };
    const resolvedHubIdentity = hubIdentityRecord ?? await loadStoreRuntimeHubIdentity();
    const nextHubIdentity = activeBranchId
      ? await ensureStoreRuntimeHubIdentity({
          accessToken: nextSession.access_token,
          tenantId: nextTenantId,
          branchId: activeBranchId,
          selectedRuntimeDeviceId: runtimeDeviceBinding.selectedRuntimeDeviceId,
          runtimeDevices: devicesResponse.records,
          runtimeShellStatus: resolvedRuntimeShellStatus,
          currentHubIdentity: resolvedHubIdentity,
        })
      : null;
    if (activeBranchId) {
      await replayPendingRuntimeActions({
        accessTokenOverride: nextSession.access_token,
        tenantIdOverride: nextTenantId,
        branchIdOverride: activeBranchId,
        selectedRuntimeDeviceIdOverride: runtimeDeviceBinding.selectedRuntimeDeviceId,
      });
    }

    sessionRecordRef.current = nextSession;
    startTransition(() => {
      setAccessToken(nextSession.access_token);
      setSessionExpiresAt(nextSession.expires_at);
      setActor(nextActor);
      setTenant(tenantSummary);
      setBranches(branchList.records);
      setBranchCatalogItems(catalogResponse.records);
      setInventorySnapshot(snapshotResponse.records);
      setSales(salesResponse.records);
      setRuntimeDevices(devicesResponse.records);
      setSelectedRuntimeDeviceId(runtimeDeviceBinding.selectedRuntimeDeviceId);
      setRuntimeDeviceClaim(runtimeDeviceBinding.runtimeDeviceClaim);
      setHubIdentityRecord(nextHubIdentity);
      setCacheStatus('SYNCED');
      setActivationCode('');
    });
  }

  async function replayPendingRuntimeActions(options?: {
    accessTokenOverride?: string;
    tenantIdOverride?: string;
    branchIdOverride?: string;
    selectedRuntimeDeviceIdOverride?: string;
  }) {
    const activeAccessToken = options?.accessTokenOverride ?? accessToken;
    const activeTenantId = options?.tenantIdOverride ?? tenantId;
    const activeBranchId = options?.branchIdOverride ?? branchId;
    const activeDeviceId = options?.selectedRuntimeDeviceIdOverride ?? selectedRuntimeDeviceId;

    if (!activeAccessToken || !activeTenantId || !activeBranchId || pendingMutations.length === 0) {
      return;
    }

    const replayResult = await replayPendingRuntimeMutations({
      accessToken: activeAccessToken,
      mutations: pendingMutations,
    });

    const shouldRefreshPrintQueue = Boolean(
      activeDeviceId && replayResult.refreshPrintQueueDeviceIds.includes(activeDeviceId),
    );
    let refreshedPrintJobs: { records: ControlPlanePrintJob[] } | null = null;
    if (shouldRefreshPrintQueue) {
      try {
        refreshedPrintJobs = await storeControlPlaneClient.listRuntimePrintJobs(
          activeAccessToken,
          activeTenantId,
          activeBranchId,
          activeDeviceId,
        );
      } catch {
        refreshedPrintJobs = null;
      }
    }

    startTransition(() => {
      setPendingMutations(replayResult.remainingMutations);
      setPendingMutationCount(replayResult.remainingMutations.length);
      if (replayResult.latestHeartbeat) {
        setRuntimeHeartbeat(replayResult.latestHeartbeat);
      }
      if (replayResult.latestPrintJob) {
        setLatestPrintJob(replayResult.latestPrintJob);
      }
      if (refreshedPrintJobs) {
        setPrintJobs(refreshedPrintJobs.records);
      }
      if (replayResult.remainingMutations.length === 0) {
        setErrorMessage('');
      }
    });
  }

  useEffect(() => {
    let isCancelled = false;

    void loadStoreRuntimeHubIdentity()
      .then((record) => {
        if (!isCancelled) {
          setHubIdentityRecord(record);
        }
      })
      .catch(() => {
        if (!isCancelled) {
          setHubIdentityRecord(null);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, []);

  useEffect(() => {
    let isCancelled = false;

    void (async () => {
      const runtimeCache = createResolvedStoreRuntimeCache();
      const cachedSnapshot = await runtimeCache.load();
      const persistence = await runtimeCache.getPersistence();
      if (isCancelled) {
        return;
      }

      setCachePersistence(persistence);
      setLastCachedAt(persistence.cached_at);

      const shouldDeferCacheHydration = runtimeShellStatus?.runtime_kind === 'packaged_desktop'
        && (!hasLoadedLocalAuth || (localAuthRecord !== null && !isLocalUnlocked));
      if (!cachedSnapshot) {
        return;
      }
      if (shouldDeferCacheHydration) {
        return;
      }
      applyCachedRuntimeSnapshot(cachedSnapshot);
    })();

    return () => {
      isCancelled = true;
    };
  }, [hasLoadedLocalAuth, isLocalUnlocked, localAuthRecord, runtimeShellStatus?.runtime_kind]);

  useEffect(() => {
    let isCancelled = false;

    void (async () => {
      const loadedLocalAuth = await loadStoreRuntimeLocalAuth();
      if (isCancelled) {
        return;
      }
      const packagedInstallationId = runtimeShellStatus?.runtime_kind === 'packaged_desktop'
        ? runtimeShellStatus.installation_id ?? null
        : null;
      if (
        loadedLocalAuth
        && packagedInstallationId
        && loadedLocalAuth.installation_id !== packagedInstallationId
      ) {
        await clearStoreRuntimeLocalAuth();
        if (!isCancelled) {
          setLocalAuthRecord(null);
          setHasLoadedLocalAuth(true);
        }
        return;
      }
      setLocalAuthRecord(loadedLocalAuth);
      setHasLoadedLocalAuth(true);
    })();

    return () => {
      isCancelled = true;
    };
  }, [runtimeShellStatus?.installation_id, runtimeShellStatus?.runtime_kind]);

  useEffect(() => {
    let isCancelled = false;

    void (async () => {
      if (!hasLoadedLocalAuth) {
        return;
      }
      const persistedSession = await loadStoreRuntimeSession();
      if (isCancelled || !persistedSession?.access_token) {
        return;
      }
      const restorePolicy = resolveStoreRuntimeSessionRestorePolicy({
        runtimeShellKind: runtimeShellStatus?.runtime_kind ?? null,
        hasLocalAuthRecord: localAuthRecord !== null,
      });
      if (restorePolicy === 'DEFER_TO_LOCAL_AUTH') {
        return;
      }
      if (restorePolicy === 'CLEAR_STALE_PACKAGED_SESSION') {
        await clearStoreRuntimeSession();
        return;
      }
      if (isStoreRuntimeSessionExpired(persistedSession)) {
        await clearStoreRuntimeSession();
        if (!isCancelled) {
          resetRuntimeWorkspaceState();
          setErrorMessage('Stored runtime session expired. Sign in again.');
        }
        return;
      }
      setIsBusy(true);
      setErrorMessage('');
      try {
        await bootstrapRuntimeSession(persistedSession);
      } catch (error) {
        await clearStoreRuntimeSession();
        if (!isCancelled) {
          resetRuntimeWorkspaceState();
          setErrorMessage(error instanceof Error ? error.message : 'Stored runtime session could not be restored');
        }
      } finally {
        if (!isCancelled) {
          setIsBusy(false);
        }
      }
    })();

    return () => {
      isCancelled = true;
    };
  }, [hasLoadedLocalAuth, localAuthRecord, runtimeShellStatus?.runtime_kind]);

  useEffect(() => {
    const hasRuntimeState =
      Boolean(actor)
      || Boolean(tenant)
      || branches.length > 0
      || branchCatalogItems.length > 0
      || inventorySnapshot.length > 0
      || sales.length > 0
      || runtimeDevices.length > 0
      || printJobs.length > 0
      || Boolean(latestSale)
      || Boolean(latestSaleReturn)
      || Boolean(latestExchange)
      || Boolean(latestPrintJob);
    if (!hasRuntimeState) {
      return;
    }
    if (!isSessionLive && cacheStatus === 'HYDRATED') {
      return;
    }

    const cachedAt = new Date().toISOString();
    const snapshot: StoreRuntimeCacheSnapshot = {
      schema_version: 1,
      cached_at: cachedAt,
      authority: 'CONTROL_PLANE_ONLY',
      actor,
      tenant,
      branches,
      branch_catalog_items: branchCatalogItems,
      inventory_snapshot: inventorySnapshot,
      sales,
      runtime_devices: runtimeDevices,
      selected_runtime_device_id: selectedRuntimeDeviceId,
      runtime_heartbeat: runtimeHeartbeat,
      print_jobs: printJobs,
      latest_print_job: latestPrintJob,
      latest_sale: latestSale,
      latest_sale_return: latestSaleReturn,
      latest_exchange: latestExchange,
      pending_mutations: pendingMutations,
    };
    const runtimeCache = createResolvedStoreRuntimeCache();
    let isCancelled = false;
    void runtimeCache.save(snapshot)
      .then((persistence) => {
        if (isCancelled) {
          return;
        }
        setCachePersistence(persistence);
        if (cacheStatus !== 'SYNCED') {
          setCacheStatus('SYNCED');
        }
        if (cacheStatus !== 'SYNCED' || !lastCachedAt) {
          setLastCachedAt(persistence.cached_at ?? cachedAt);
        }
        setPendingMutationCount(pendingMutations.length);
      })
      .catch(() => {
        if (!isCancelled) {
          setCachePersistence({
            backend_kind: 'unavailable',
            backend_label: 'Runtime cache unavailable',
            cached_at: null,
            detail: 'Runtime cache persistence failed for this shell.',
            location: null,
            snapshot_present: false,
          });
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [
    actor,
    branchCatalogItems,
    branches,
    cacheStatus,
    inventorySnapshot,
    isSessionLive,
    lastCachedAt,
    latestExchange,
    latestPrintJob,
    latestSale,
    latestSaleReturn,
    pendingMutationCount,
    pendingMutations,
    printJobs,
    runtimeDevices,
    runtimeHeartbeat,
    sales,
    selectedRuntimeDeviceId,
    tenant,
  ]);

  async function startSession() {
    if (!supportsDeveloperSessionBootstrap) {
      setErrorMessage('Browser preview does not support manual session bootstrap. Use the approved packaged desktop activation flow.');
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const session = await storeControlPlaneClient.exchangeSession(korsenexToken);
      await bootstrapRuntimeSession(session);
      await saveStoreRuntimeSession({ access_token: session.access_token, expires_at: session.expires_at });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to start runtime session');
    } finally {
      setIsBusy(false);
    }
  }

  async function activateDesktopAccess() {
    if (!runtimeShellStatus?.installation_id || !activationCode) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const session = await storeControlPlaneClient.activateStoreDesktopSession(
        runtimeShellStatus.installation_id,
        activationCode,
      );
      startTransition(() => {
        setPendingPinEnrollmentSession(session);
        setNewPin('');
        setConfirmPin('');
        setActivationCode('');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to activate desktop access');
    } finally {
      setIsBusy(false);
    }
  }

  async function enrollRuntimePin() {
    if (!pendingPinEnrollmentSession || !runtimeShellStatus?.installation_id) {
      return;
    }
    const normalizedNewPin = newPin.trim();
    const normalizedConfirmPin = confirmPin.trim();
    if (!isStoreRuntimePinFormatValid(normalizedNewPin)) {
      setErrorMessage('PIN must be exactly 4 digits.');
      return;
    }
    if (normalizedNewPin !== normalizedConfirmPin) {
      setErrorMessage('PIN confirmation did not match.');
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const pinSalt = createStoreRuntimePinSalt();
      const pinHash = await hashStoreRuntimePin(normalizedNewPin, pinSalt);
      const localAuthRecordToSave: StoreRuntimeLocalAuthRecord = {
        schema_version: STORE_RUNTIME_LOCAL_AUTH_SCHEMA_VERSION,
        installation_id: runtimeShellStatus.installation_id,
        device_id: pendingPinEnrollmentSession.device_id,
        staff_profile_id: pendingPinEnrollmentSession.staff_profile_id,
        local_auth_token: pendingPinEnrollmentSession.local_auth_token,
        activation_version: pendingPinEnrollmentSession.activation_version,
        offline_valid_until: pendingPinEnrollmentSession.offline_valid_until,
        pin_attempt_limit: STORE_RUNTIME_PIN_ATTEMPT_LIMIT,
        pin_lockout_seconds: STORE_RUNTIME_PIN_LOCKOUT_SECONDS,
        pin_salt: pinSalt,
        pin_hash: pinHash,
        failed_attempts: 0,
        locked_until: null,
        enrolled_at: new Date().toISOString(),
        last_unlocked_at: new Date().toISOString(),
      };
      await saveStoreRuntimeLocalAuth(localAuthRecordToSave);
      await saveStoreRuntimeSession({
        access_token: pendingPinEnrollmentSession.access_token,
        expires_at: pendingPinEnrollmentSession.expires_at,
      });
      setLocalAuthRecord(localAuthRecordToSave);
      setIsLocalUnlocked(true);
      setPendingPinEnrollmentSession(null);
      setNewPin('');
      setConfirmPin('');
      await bootstrapRuntimeSession(pendingPinEnrollmentSession);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to save runtime PIN');
      return;
    } finally {
      setIsBusy(false);
    }
  }

  async function unlockRuntimeWithPin() {
    if (!localAuthRecord || !runtimeShellStatus?.installation_id) {
      return;
    }
    if (isStoreRuntimePinLocked(localAuthRecord)) {
      setErrorMessage('Runtime PIN is temporarily locked. Try again later.');
      return;
    }
    if (!isStoreRuntimePinFormatValid(unlockPin)) {
      setErrorMessage('PIN must be exactly 4 digits.');
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const pinMatches = await verifyStoreRuntimePin(unlockPin, localAuthRecord);
      if (!pinMatches) {
        const failedLocalAuth = recordFailedStoreRuntimePinAttempt(localAuthRecord);
        await saveStoreRuntimeLocalAuth(failedLocalAuth);
        setLocalAuthRecord(failedLocalAuth);
        setErrorMessage(
          failedLocalAuth.locked_until
            ? 'Runtime PIN is temporarily locked due to repeated failures.'
            : 'PIN did not match this device.',
        );
        return;
      }

      const persistedSession = await loadStoreRuntimeSession();
      if (persistedSession?.access_token && !isStoreRuntimeSessionExpired(persistedSession)) {
        const updatedLocalAuth = recordSuccessfulStoreRuntimePinUnlock(localAuthRecord);
        await saveStoreRuntimeLocalAuth(updatedLocalAuth);
        setLocalAuthRecord(updatedLocalAuth);
        setIsLocalUnlocked(true);
        setUnlockPin('');
        await bootstrapRuntimeSession(persistedSession);
        return;
      }
      if (persistedSession?.access_token) {
        await clearStoreRuntimeSession();
      }

      try {
        const session = await storeControlPlaneClient.unlockStoreDesktopSession(
          runtimeShellStatus.installation_id,
          localAuthRecord.local_auth_token,
        );
        const updatedLocalAuth = recordSuccessfulStoreRuntimePinUnlock(
          {
            ...localAuthRecord,
            local_auth_token: session.local_auth_token,
            activation_version: session.activation_version,
          },
          {
            offlineValidUntil: session.offline_valid_until,
          },
        );
        await saveStoreRuntimeLocalAuth(updatedLocalAuth);
        await saveStoreRuntimeSession({
          access_token: session.access_token,
          expires_at: session.expires_at,
        });
        setLocalAuthRecord(updatedLocalAuth);
        setIsLocalUnlocked(true);
        setUnlockPin('');
        await bootstrapRuntimeSession(session);
        return;
      } catch (error) {
        if (error instanceof ControlPlaneRequestError && (error.status === 401 || error.status === 403 || error.status === 409)) {
          await clearStoreRuntimeSession();
          await clearStoreRuntimeLocalAuth();
          setLocalAuthRecord(null);
          resetRuntimeWorkspaceState();
          setErrorMessage('Runtime unlock is no longer valid. Ask the owner to issue a new activation.');
          return;
        }
        if (!isStoreRuntimeLocalAuthOfflineExpired(localAuthRecord)) {
          const updatedLocalAuth = recordSuccessfulStoreRuntimePinUnlock(localAuthRecord);
          await saveStoreRuntimeLocalAuth(updatedLocalAuth);
          setLocalAuthRecord(updatedLocalAuth);
          setIsLocalUnlocked(true);
          setUnlockPin('');
          setErrorMessage('Control plane unavailable. Cached runtime unlocked locally.');
          return;
        }
        setErrorMessage('Offline runtime unlock expired. Reconnect to the control plane to continue.');
        return;
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to unlock runtime');
    } finally {
      setIsBusy(false);
    }
  }

  async function refreshRuntimeSession() {
    const currentAccessToken = sessionRecordRef.current?.access_token ?? accessToken;
    if (!currentAccessToken) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const session = await storeControlPlaneClient.refreshSession(currentAccessToken);
      await bootstrapRuntimeSession(session);
      await saveStoreRuntimeSession({ access_token: session.access_token, expires_at: session.expires_at });
    } catch (error) {
      if (error instanceof ControlPlaneRequestError && error.status === 401) {
        await clearStoreRuntimeSession();
        resetRuntimeWorkspaceState();
        setErrorMessage('Runtime session expired. Sign in again.');
      } else {
        setErrorMessage(error instanceof Error ? error.message : 'Unable to refresh runtime session');
      }
    } finally {
      setIsBusy(false);
    }
  }

  async function signOut() {
    const currentAccessToken = sessionRecordRef.current?.access_token ?? accessToken;
    setIsBusy(true);
    setErrorMessage('');
    try {
      if (currentAccessToken) {
        await storeControlPlaneClient.signOut(currentAccessToken);
      }
      await clearStoreRuntimeSession();
      resetRuntimeWorkspaceState();
      if (localAuthRecord) {
        setErrorMessage('Runtime session signed out. Unlock with PIN to continue on this device.');
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to sign out of the runtime session');
    } finally {
      setIsBusy(false);
    }
  }

  async function createSalesInvoice() {
    const catalogItem = branchCatalogItems[0];
    if (!accessToken || !tenantId || !branchId || !catalogItem) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const sale = await storeControlPlaneClient.createSale(accessToken, tenantId, branchId, {
        customer_name: customerName,
        customer_gstin: customerGstin || null,
        payment_method: paymentMethod,
        lines: [{ product_id: catalogItem.product_id, quantity: Number(saleQuantity) }],
      });
      const [salesResponse, snapshotResponse] = await Promise.all([
        storeControlPlaneClient.listSales(accessToken, tenantId, branchId),
        storeControlPlaneClient.listInventorySnapshot(accessToken, tenantId, branchId),
      ]);
      startTransition(() => {
        setLatestSale(sale);
        setSales(salesResponse.records);
        setInventorySnapshot(snapshotResponse.records);
        setLatestPrintJob(null);
        setCustomerName('');
        setCustomerGstin('');
        setSaleQuantity('1');
        setReturnQuantity('1');
        setRefundAmount(String(sale.payment.amount));
        setRefundMethod(sale.payment.payment_method);
        setExchangeReturnQuantity('1');
        setReplacementQuantity('1');
        setExchangeSettlementMethod('Cash');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to create sales invoice');
    } finally {
      setIsBusy(false);
    }
  }

  async function lookupScannedBarcode() {
    if (!accessToken || !tenantId || !branchId || !scannedBarcode) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const lookup = await storeControlPlaneClient.lookupCatalogScan(accessToken, tenantId, branchId, scannedBarcode);
      startTransition(() => {
        setLatestScanLookup(lookup);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to look up scanned barcode');
    } finally {
      setIsBusy(false);
    }
  }

  async function createExchange() {
    const sale = latestSale;
    const saleLine = sale?.lines[0];
    if (!accessToken || !tenantId || !branchId || !sale || !saleLine) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const exchange = await storeControlPlaneClient.createExchange(accessToken, tenantId, branchId, sale.id, {
        settlement_method: exchangeSettlementMethod,
        return_lines: [{ product_id: saleLine.product_id, quantity: Number(exchangeReturnQuantity) }],
        replacement_lines: [{ product_id: saleLine.product_id, quantity: Number(replacementQuantity) }],
      });
      const snapshotResponse = await storeControlPlaneClient.listInventorySnapshot(accessToken, tenantId, branchId);
      startTransition(() => {
        setLatestExchange(exchange);
        setLatestSaleReturn(exchange.sale_return);
        setLatestSale(exchange.replacement_sale);
        setInventorySnapshot(snapshotResponse.records);
        setLatestPrintJob(null);
        setExchangeReturnQuantity('1');
        setReplacementQuantity('1');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to create exchange');
    } finally {
      setIsBusy(false);
    }
  }

  async function createSaleReturn() {
    const sale = latestSale;
    const saleLine = sale?.lines[0];
    if (!accessToken || !tenantId || !branchId || !sale || !saleLine) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const saleReturn = await storeControlPlaneClient.createSaleReturn(accessToken, tenantId, branchId, sale.id, {
        refund_amount: Number(refundAmount),
        refund_method: refundMethod,
        lines: [{ product_id: saleLine.product_id, quantity: Number(returnQuantity) }],
      });
      const snapshotResponse = await storeControlPlaneClient.listInventorySnapshot(accessToken, tenantId, branchId);
      startTransition(() => {
        setLatestSaleReturn(saleReturn);
        setInventorySnapshot(snapshotResponse.records);
        setLatestPrintJob(null);
        setReturnQuantity('1');
        setRefundAmount('');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to create sale return');
    } finally {
      setIsBusy(false);
    }
  }

  async function loadBatchExpiryReport() {
    if (!accessToken || !tenantId || !branchId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const report = await storeControlPlaneClient.getBatchExpiryReport(accessToken, tenantId, branchId);
      startTransition(() => {
        setBatchExpiryReport(report);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to load branch expiry report');
    } finally {
      setIsBusy(false);
    }
  }

  async function createBatchExpiryWriteOff() {
    const firstBatchLot = batchExpiryReport?.records[0];
    if (!accessToken || !tenantId || !branchId || !firstBatchLot) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const writeOff = await storeControlPlaneClient.createBatchExpiryWriteOff(accessToken, tenantId, branchId, firstBatchLot.batch_lot_id, {
        quantity: Number(expiryWriteOffQuantity),
        reason: expiryWriteOffReason,
      });
      const [report, snapshot] = await Promise.all([
        storeControlPlaneClient.getBatchExpiryReport(accessToken, tenantId, branchId),
        storeControlPlaneClient.listInventorySnapshot(accessToken, tenantId, branchId),
      ]);
      startTransition(() => {
        setLatestBatchWriteOff(writeOff);
        setBatchExpiryReport(report);
        setInventorySnapshot(snapshot.records);
        setExpiryWriteOffQuantity('1');
        setExpiryWriteOffReason('');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to write off batch lot');
    } finally {
      setIsBusy(false);
    }
  }

  async function queueLatestInvoicePrint() {
    if (!accessToken || !tenantId || !branchId || !latestSale || !selectedRuntimeDeviceId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const printJob = await storeControlPlaneClient.queueSaleInvoicePrintJob(accessToken, tenantId, branchId, latestSale.id, {
        device_id: selectedRuntimeDeviceId,
        copies: 1,
      });
      startTransition(() => {
        setLatestPrintJob(printJob);
      });
    } catch (error) {
      if (shouldQueueRuntimeOutboxMutation(error)) {
        queuePendingMutation(
          createPendingSalesInvoicePrintMutation({
            tenantId,
            branchId,
            deviceId: selectedRuntimeDeviceId,
            saleId: latestSale.id,
            documentNumber: latestSale.invoice_number,
            copies: 1,
          }),
          'Control plane unavailable. The invoice print request is queued locally for replay.',
        );
        return;
      }
      setErrorMessage(error instanceof Error ? error.message : 'Unable to queue invoice print job');
    } finally {
      setIsBusy(false);
    }
  }

  async function queueLatestCreditNotePrint() {
    if (!accessToken || !tenantId || !branchId || !latestSaleReturn || !selectedRuntimeDeviceId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const printJob = await storeControlPlaneClient.queueSaleReturnPrintJob(
        accessToken,
        tenantId,
        branchId,
        latestSaleReturn.id,
        {
          device_id: selectedRuntimeDeviceId,
          copies: 1,
        },
      );
      startTransition(() => {
        setLatestPrintJob(printJob);
      });
    } catch (error) {
      if (shouldQueueRuntimeOutboxMutation(error)) {
        queuePendingMutation(
          createPendingCreditNotePrintMutation({
            tenantId,
            branchId,
            deviceId: selectedRuntimeDeviceId,
            saleReturnId: latestSaleReturn.id,
            documentNumber: latestSaleReturn.credit_note.credit_note_number,
            copies: 1,
          }),
          'Control plane unavailable. The credit note print request is queued locally for replay.',
        );
        return;
      }
      setErrorMessage(error instanceof Error ? error.message : 'Unable to queue credit note print job');
    } finally {
      setIsBusy(false);
    }
  }

  async function heartbeatRuntimeDevice() {
    if (!accessToken || !tenantId || !branchId || !selectedRuntimeDeviceId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const heartbeat = await storeControlPlaneClient.heartbeatRuntimeDevice(
        accessToken,
        tenantId,
        branchId,
        selectedRuntimeDeviceId,
      );
      startTransition(() => {
        setRuntimeHeartbeat(heartbeat);
      });
    } catch (error) {
      if (shouldQueueRuntimeOutboxMutation(error)) {
        queuePendingMutation(
          createPendingHeartbeatMutation({
            tenantId,
            branchId,
            deviceId: selectedRuntimeDeviceId,
          }),
          'Control plane unavailable. The runtime heartbeat is queued locally for replay.',
        );
        return;
      }
      setErrorMessage(error instanceof Error ? error.message : 'Unable to send runtime device heartbeat');
    } finally {
      setIsBusy(false);
    }
  }

  async function refreshPrintQueue() {
    if (!accessToken || !tenantId || !branchId || !selectedRuntimeDeviceId) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const response = await storeControlPlaneClient.listRuntimePrintJobs(
        accessToken,
        tenantId,
        branchId,
        selectedRuntimeDeviceId,
      );
      startTransition(() => {
        setPrintJobs(response.records);
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to refresh runtime print queue');
    } finally {
      setIsBusy(false);
    }
  }

  async function completeFirstPrintJob() {
    const firstJob = printJobs[0];
    if (!accessToken || !tenantId || !branchId || !selectedRuntimeDeviceId || !firstJob) {
      return;
    }
    setIsBusy(true);
    setErrorMessage('');
    try {
      const completed = await storeControlPlaneClient.completeRuntimePrintJob(
        accessToken,
        tenantId,
        branchId,
        selectedRuntimeDeviceId,
        firstJob.id,
        { status: 'COMPLETED' },
      );
      startTransition(() => {
        setLatestPrintJob(completed);
        setPrintJobs((currentJobs) => currentJobs.filter((job) => job.id !== firstJob.id));
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to complete runtime print job');
    } finally {
      setIsBusy(false);
    }
  }

  return {
    accessToken,
    actor,
    batchExpiryReport,
    branchCatalogItems,
    branchId,
    branches,
    cacheBackendDetail: cachePersistence.detail,
    cacheBackendKind: cachePersistence.backend_kind,
    cacheBackendLabel: cachePersistence.backend_label,
    cacheBackendLocation: cachePersistence.location,
    cacheStatus,
    confirmPin,
    activationCode,
    scannedBarcode,
    activateDesktopAccess,
    enrollRuntimePin,
    createExchange,
    createBatchExpiryWriteOff,
    createSaleReturn,
    createSalesInvoice,
    customerGstin,
    customerName,
    errorMessage,
    expiryWriteOffQuantity,
    expiryWriteOffReason,
    exchangeReturnQuantity,
    exchangeSettlementMethod,
    heartbeatRuntimeDevice,
    inventorySnapshot,
    isSessionLive,
    isBusy,
    hasLoadedLocalAuth,
    korsenexToken,
    lastCachedAt,
    localAuthRecord,
    latestPrintJob,
    latestBatchWriteOff,
    latestScanLookup,
    latestSale,
    latestSaleReturn,
    latestExchange,
    paymentMethod,
    pendingMutationCount,
    pendingRuntimeMutations: pendingMutations,
    printJobs,
    loadBatchExpiryReport,
    queueLatestCreditNotePrint,
    queueLatestInvoicePrint,
    replayPendingRuntimeActions: replayPendingRuntimeActions,
    refreshPrintQueue,
    runtimeAppVersion: runtimeShellStatus?.app_version ?? null,
    runtimeArchitecture: runtimeShellStatus?.architecture ?? null,
    runtimeCacheDatabasePath: runtimeShellStatus?.cache_db_path ?? null,
    runtimeDevices,
    runtimeHeartbeat,
    runtimeHome: runtimeShellStatus?.runtime_home ?? null,
    runtimeHostname: runtimeShellStatus?.hostname ?? null,
    runtimeInstallationId: runtimeShellStatus?.installation_id ?? null,
    runtimeClaimCode: runtimeDeviceClaim?.claim_code ?? runtimeShellStatus?.claim_code ?? null,
    runtimeBindingStatus: runtimeDeviceClaim?.status ?? (runtimeShellStatus?.runtime_kind === 'packaged_desktop' ? 'UNBOUND' : 'BROWSER_MANAGED'),
    runtimeHubDeviceCode: hubIdentityRecord?.device_code ?? null,
    runtimeHubIdentityState: hubIdentityRecord ? 'READY' : 'NOT_CONFIGURED',
    runtimeHubIssuedAt: hubIdentityRecord?.issued_at ?? null,
    runtimeHubManifestUrl: runtimeShellStatus?.hub_manifest_url ?? null,
    runtimeHubServiceState: runtimeShellStatus?.hub_service_state ?? null,
    runtimeHubServiceUrl: runtimeShellStatus?.hub_service_url ?? null,
    runtimeOperatingSystem: runtimeShellStatus?.operating_system ?? null,
    runtimeShellBridgeState: runtimeShellStatus?.bridge_state ?? 'unavailable',
    runtimeShellError,
    runtimeShellKind: runtimeShellStatus?.runtime_kind ?? null,
    runtimeShellLabel: runtimeShellStatus?.runtime_label ?? null,
    runtimeDeviceClaim,
    supportsDeveloperSessionBootstrap,
    requiresLocalUnlock,
    requiresPinEnrollment,
    replacementQuantity,
    refundAmount,
    refundMethod,
    refreshRuntimeSession,
    returnQuantity,
    saleQuantity,
    sales,
    sessionExpiresAt,
    selectedRuntimeDeviceId,
    setConfirmPin,
    setCustomerGstin,
    setCustomerName,
    setExpiryWriteOffQuantity,
    setExpiryWriteOffReason,
    setExchangeReturnQuantity,
    setExchangeSettlementMethod,
    setActivationCode,
    setKorsenexToken,
    setNewPin,
    setPaymentMethod,
    setScannedBarcode,
    setSelectedRuntimeDeviceId,
    setReplacementQuantity,
    setRefundAmount,
    setRefundMethod,
    setReturnQuantity,
    setSaleQuantity,
    setUnlockPin,
    signOut,
    startSession,
    tenantId,
    tenant,
    completeFirstPrintJob,
    lookupScannedBarcode,
    newPin,
    unlockPin,
    unlockRuntimeWithPin,
  };
}

export type StoreRuntimeWorkspaceState = ReturnType<typeof useStoreRuntimeWorkspace>;
