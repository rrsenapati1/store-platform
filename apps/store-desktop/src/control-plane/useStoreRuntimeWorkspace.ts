import { startTransition, useEffect, useState } from 'react';
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
  ControlPlaneTenant,
} from '@store/types';
import { storeControlPlaneClient } from './client';
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
import { loadStoreRuntimeShellStatus, useStoreRuntimeShellStatus } from './useStoreRuntimeShellStatus';

type CacheStatus = 'EMPTY' | 'HYDRATED' | 'SYNCED';

export function useStoreRuntimeWorkspace() {
  const {
    runtimeShellError,
    runtimeShellStatus,
  } = useStoreRuntimeShellStatus();
  const [korsenexToken, setKorsenexToken] = useState('');
  const [accessToken, setAccessToken] = useState('');
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
  const isSessionLive = Boolean(accessToken);

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

    void (async () => {
      const runtimeCache = createResolvedStoreRuntimeCache();
      const cachedSnapshot = await runtimeCache.load();
      const persistence = await runtimeCache.getPersistence();
      if (isCancelled) {
        return;
      }

      setCachePersistence(persistence);
      setLastCachedAt(persistence.cached_at);

      if (!cachedSnapshot) {
        return;
      }

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
    })();

    return () => {
      isCancelled = true;
    };
  }, []);

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
    setIsBusy(true);
    setErrorMessage('');
    try {
      const session = await storeControlPlaneClient.exchangeSession(korsenexToken);
      const nextActor = await storeControlPlaneClient.getActor(session.access_token);
      const nextTenantId = nextActor.tenant_memberships[0]?.tenant_id ?? nextActor.branch_memberships[0]?.tenant_id;
      if (!nextTenantId) {
        throw new Error('Runtime session is not bound to a tenant');
      }
      const tenantSummary = await storeControlPlaneClient.getTenantSummary(session.access_token, nextTenantId);
      const branchList = await storeControlPlaneClient.listBranches(session.access_token, nextTenantId);
      const activeBranchId = nextActor.branch_memberships[0]?.branch_id ?? branchList.records[0]?.branch_id;
      const resolvedRuntimeShellStatus = await loadStoreRuntimeShellStatus().catch(() => runtimeShellStatus);
      const [catalogResponse, snapshotResponse, salesResponse, devicesResponse] = activeBranchId
        ? await Promise.all([
            storeControlPlaneClient.listBranchCatalogItems(session.access_token, nextTenantId, activeBranchId),
            storeControlPlaneClient.listInventorySnapshot(session.access_token, nextTenantId, activeBranchId),
            storeControlPlaneClient.listSales(session.access_token, nextTenantId, activeBranchId),
            storeControlPlaneClient.listRuntimeDevices(session.access_token, nextTenantId, activeBranchId),
          ])
        : [{ records: [] }, { records: [] }, { records: [] }, { records: [] }];
      const runtimeDeviceBinding = activeBranchId
        ? await resolveStoreRuntimeDeviceBinding({
            accessToken: session.access_token,
            tenantId: nextTenantId,
            branchId: activeBranchId,
            runtimeDevices: devicesResponse.records,
            runtimeShellStatus: resolvedRuntimeShellStatus,
          })
        : { selectedRuntimeDeviceId: '', runtimeDeviceClaim: null };
      if (activeBranchId) {
        await replayPendingRuntimeActions({
          accessTokenOverride: session.access_token,
          tenantIdOverride: nextTenantId,
          branchIdOverride: activeBranchId,
          selectedRuntimeDeviceIdOverride: runtimeDeviceBinding.selectedRuntimeDeviceId,
        });
      }

      startTransition(() => {
        setAccessToken(session.access_token);
        setActor(nextActor);
        setTenant(tenantSummary);
        setBranches(branchList.records);
        setBranchCatalogItems(catalogResponse.records);
        setInventorySnapshot(snapshotResponse.records);
        setSales(salesResponse.records);
        setRuntimeDevices(devicesResponse.records);
        setSelectedRuntimeDeviceId(runtimeDeviceBinding.selectedRuntimeDeviceId);
        setRuntimeDeviceClaim(runtimeDeviceBinding.runtimeDeviceClaim);
        setCacheStatus('SYNCED');
      });
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to start runtime session');
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
    scannedBarcode,
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
    korsenexToken,
    lastCachedAt,
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
    runtimeOperatingSystem: runtimeShellStatus?.operating_system ?? null,
    runtimeShellBridgeState: runtimeShellStatus?.bridge_state ?? 'unavailable',
    runtimeShellError,
    runtimeShellKind: runtimeShellStatus?.runtime_kind ?? null,
    runtimeShellLabel: runtimeShellStatus?.runtime_label ?? null,
    runtimeDeviceClaim,
    replacementQuantity,
    refundAmount,
    refundMethod,
    returnQuantity,
    saleQuantity,
    sales,
    selectedRuntimeDeviceId,
    setCustomerGstin,
    setCustomerName,
    setExpiryWriteOffQuantity,
    setExpiryWriteOffReason,
    setExchangeReturnQuantity,
    setExchangeSettlementMethod,
    setKorsenexToken,
    setPaymentMethod,
    setScannedBarcode,
    setSelectedRuntimeDeviceId,
    setReplacementQuantity,
    setRefundAmount,
    setRefundMethod,
    setReturnQuantity,
    setSaleQuantity,
    startSession,
    tenantId,
    tenant,
    completeFirstPrintJob,
    lookupScannedBarcode,
  };
}

export type StoreRuntimeWorkspaceState = ReturnType<typeof useStoreRuntimeWorkspace>;
