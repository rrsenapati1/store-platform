package com.store.mobile.ui

import android.content.Context
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.store.mobile.StoreMobileAppBootstrap
import com.store.mobile.StoreMobileApplication
import com.store.mobile.MainActivity
import com.store.mobile.controlplane.StoreMobileControlPlaneClient
import com.store.mobile.operations.InMemoryExpiryRepository
import com.store.mobile.operations.InMemoryReceivingRepository
import com.store.mobile.operations.InMemoryRestockRepository
import com.store.mobile.operations.InMemoryStockCountRepository
import com.store.mobile.operations.ExpiryRepository
import com.store.mobile.operations.ReceivingRepository
import com.store.mobile.operations.RemoteExpiryRepository
import com.store.mobile.operations.RemoteReceivingRepository
import com.store.mobile.operations.RemoteRestockRepository
import com.store.mobile.operations.RemoteStockCountRepository
import com.store.mobile.operations.RestockRepository
import com.store.mobile.operations.StockCountRepository
import com.store.mobile.runtime.FakeStoreMobileHubClient
import com.store.mobile.runtime.SharedPreferencesStoreMobileKeyValueStore
import com.store.mobile.runtime.StoreMobilePairedDevice
import com.store.mobile.runtime.StoreMobilePairingRepository
import com.store.mobile.runtime.StoreMobilePersistentPairingRepository
import com.store.mobile.runtime.StoreMobilePersistentSessionRepository
import com.store.mobile.runtime.StoreMobileRuntimeSession
import com.store.mobile.runtime.StoreMobileSessionRepository
import com.store.mobile.runtime.parseStoreMobileExpiryMillis
import com.store.mobile.scan.ExternalScannerEvent
import com.store.mobile.scan.InMemoryScanLookupRepository
import com.store.mobile.scan.RemoteScanLookupRepository
import com.store.mobile.scan.ScanLookupRepository
import com.store.mobile.scan.ZebraDataWedgeResult
import com.store.mobile.ui.entry.StoreMobileEntrySurface
import com.store.mobile.ui.handheld.HandheldStoreShell
import com.store.mobile.ui.operations.ExpiryScreenActions
import com.store.mobile.ui.operations.ExpiryViewModel
import com.store.mobile.ui.operations.MobileOperationsSection
import com.store.mobile.ui.operations.ReceivingScreenActions
import com.store.mobile.ui.operations.ReceivingViewModel
import com.store.mobile.ui.operations.RestockScreenActions
import com.store.mobile.ui.operations.RestockViewModel
import com.store.mobile.ui.operations.StockCountScreenActions
import com.store.mobile.ui.operations.StockCountViewModel
import com.store.mobile.ui.pairing.PairingSessionStatus
import com.store.mobile.ui.pairing.PairingViewModel
import com.store.mobile.ui.runtime.buildRuntimeStatusState
import com.store.mobile.ui.scan.ScanLookupViewModel
import com.store.mobile.ui.tablet.InventoryTabletShell
import com.store.mobile.ui.theme.StoreMobileTheme

private const val STORE_MOBILE_RUNTIME_PREFERENCES = "store.mobile.runtime"

internal fun resolveStoreMobileOperationsBranchId(
    pairedDevice: StoreMobilePairedDevice?,
    session: StoreMobileRuntimeSession?,
): String? {
    return session?.branchId?.takeIf { it.isNotBlank() }
        ?: pairedDevice?.branchId?.takeIf { it.isNotBlank() }
}

internal fun isStoreMobileRuntimeSessionExpired(session: StoreMobileRuntimeSession, nowMillis: Long = System.currentTimeMillis()): Boolean {
    val expiresAtMillis = parseStoreMobileExpiryMillis(session.expiresAt)
        ?: return true
    return expiresAtMillis <= nowMillis
}

internal fun buildStoreMobileStockCountRepository(
    pairedDevice: StoreMobilePairedDevice?,
    session: StoreMobileRuntimeSession?,
): StockCountRepository {
    if (pairedDevice != null && session != null && session.accessToken.isNotBlank()) {
        return RemoteStockCountRepository(
            tenantId = session.tenantId,
            client = StoreMobileControlPlaneClient(
                baseUrl = pairedDevice.hubBaseUrl,
                accessToken = session.accessToken,
            ),
        )
    }
    return InMemoryStockCountRepository()
}

internal fun buildStoreMobileReceivingRepository(
    pairedDevice: StoreMobilePairedDevice?,
    session: StoreMobileRuntimeSession?,
): ReceivingRepository {
    if (pairedDevice != null && session != null && session.accessToken.isNotBlank()) {
        return RemoteReceivingRepository(
            tenantId = session.tenantId,
            client = StoreMobileControlPlaneClient(
                baseUrl = pairedDevice.hubBaseUrl,
                accessToken = session.accessToken,
            ),
        )
    }
    return InMemoryReceivingRepository()
}

internal fun buildStoreMobileExpiryRepository(
    pairedDevice: StoreMobilePairedDevice?,
    session: StoreMobileRuntimeSession?,
): ExpiryRepository {
    if (pairedDevice != null && session != null && session.accessToken.isNotBlank()) {
        return RemoteExpiryRepository(
            tenantId = session.tenantId,
            client = StoreMobileControlPlaneClient(
                baseUrl = pairedDevice.hubBaseUrl,
                accessToken = session.accessToken,
            ),
        )
    }
    return InMemoryExpiryRepository()
}

internal fun buildStoreMobileRestockRepository(
    pairedDevice: StoreMobilePairedDevice?,
    session: StoreMobileRuntimeSession?,
): RestockRepository {
    if (pairedDevice != null && session != null && session.accessToken.isNotBlank()) {
        return RemoteRestockRepository(
            tenantId = session.tenantId,
            client = StoreMobileControlPlaneClient(
                baseUrl = pairedDevice.hubBaseUrl,
                accessToken = session.accessToken,
            ),
        )
    }
    return InMemoryRestockRepository()
}

internal fun buildStoreMobileScanLookupRepository(
    pairedDevice: StoreMobilePairedDevice?,
    session: StoreMobileRuntimeSession?,
): ScanLookupRepository {
    if (pairedDevice != null && session != null && session.accessToken.isNotBlank()) {
        return RemoteScanLookupRepository(
            tenantId = session.tenantId,
            branchId = session.branchId,
            client = StoreMobileControlPlaneClient(
                baseUrl = pairedDevice.hubBaseUrl,
                accessToken = session.accessToken,
            ),
        )
    }
    return InMemoryScanLookupRepository()
}

@Composable
fun StoreMobileApp() {
    val context = LocalContext.current
    val application = remember(context) { context.applicationContext as? StoreMobileApplication }
    val activity = remember(context) { context as? MainActivity }
    val runtimePreferences = remember(context) {
        context.applicationContext.getSharedPreferences(
            STORE_MOBILE_RUNTIME_PREFERENCES,
            Context.MODE_PRIVATE,
        )
    }
    val keyValueStore = remember(runtimePreferences) {
        SharedPreferencesStoreMobileKeyValueStore(runtimePreferences)
    }
    val pairingRepository: StoreMobilePairingRepository = remember(keyValueStore) {
        StoreMobilePersistentPairingRepository(keyValueStore)
    }
    val sessionRepository: StoreMobileSessionRepository = remember(keyValueStore) {
        StoreMobilePersistentSessionRepository(keyValueStore)
    }
    val pairingViewModel = remember {
        PairingViewModel(
            pairingRepository = pairingRepository,
            sessionRepository = sessionRepository,
            hubClient = FakeStoreMobileHubClient(),
        )
    }
    var pairingState by remember { mutableStateOf(pairingViewModel.state) }
    val currentSession = sessionRepository.loadSession()
        ?.takeIf { it.accessToken.isNotBlank() && !isStoreMobileRuntimeSessionExpired(it) }
    val hasActiveRuntimeSession = pairingState.sessionStatus == PairingSessionStatus.ACTIVE && currentSession != null
    val operationsBranchId = resolveStoreMobileOperationsBranchId(
        pairedDevice = pairingState.pairedDevice,
        session = currentSession,
    )
    val stockCountRepository = remember(pairingState.pairedDevice, currentSession) {
        buildStoreMobileStockCountRepository(
            pairedDevice = pairingState.pairedDevice,
            session = currentSession,
        )
    }
    val receivingRepository = remember(pairingState.pairedDevice, currentSession) {
        buildStoreMobileReceivingRepository(
            pairedDevice = pairingState.pairedDevice,
            session = currentSession,
        )
    }
    val expiryRepository = remember(pairingState.pairedDevice, currentSession) {
        buildStoreMobileExpiryRepository(
            pairedDevice = pairingState.pairedDevice,
            session = currentSession,
        )
    }
    val restockRepository = remember(pairingState.pairedDevice, currentSession) {
        buildStoreMobileRestockRepository(
            pairedDevice = pairingState.pairedDevice,
            session = currentSession,
        )
    }
    val scanLookupRepository = remember(pairingState.pairedDevice, currentSession) {
        buildStoreMobileScanLookupRepository(
            pairedDevice = pairingState.pairedDevice,
            session = currentSession,
        )
    }
    val scanLookupViewModel = remember(scanLookupRepository) {
        ScanLookupViewModel(repository = scanLookupRepository)
    }
    val receivingViewModel = remember(receivingRepository) {
        ReceivingViewModel(repository = receivingRepository)
    }
    val restockViewModel = remember(restockRepository) {
        RestockViewModel(repository = restockRepository)
    }
    val stockCountViewModel = remember(stockCountRepository) {
        StockCountViewModel(repository = stockCountRepository)
    }
    val expiryViewModel = remember(expiryRepository) {
        ExpiryViewModel(repository = expiryRepository)
    }
    var scanLookupState by remember(scanLookupViewModel) { mutableStateOf(scanLookupViewModel.state) }
    var receivingState by remember(receivingViewModel) { mutableStateOf(receivingViewModel.state) }
    var stockCountState by remember(stockCountViewModel) { mutableStateOf(stockCountViewModel.state) }
    var restockState by remember { mutableStateOf(restockViewModel.state) }
    var expiryState by remember { mutableStateOf(expiryViewModel.state) }
    var handheldSection by remember { mutableStateOf(MobileOperationsSection.SCAN) }
    var tabletSection by remember { mutableStateOf(MobileOperationsSection.RECEIVING) }
    val receivingActions = remember(receivingViewModel) {
        ReceivingScreenActions(
            onLineReceivedQuantityChange = { productId, value ->
                receivingViewModel.updateLineReceivedQuantity(productId, value)
                receivingState = receivingViewModel.state
            },
            onLineDiscrepancyNoteChange = { productId, value ->
                receivingViewModel.updateLineDiscrepancyNote(productId, value)
                receivingState = receivingViewModel.state
            },
            onReceiptNoteChange = { value ->
                receivingViewModel.updateReceiptNote(value)
                receivingState = receivingViewModel.state
            },
            onSubmitReviewedReceipt = {
                receivingViewModel.submitReviewedReceipt()
                receivingState = receivingViewModel.state
            },
        )
    }
    val stockCountActions = remember(stockCountViewModel) {
        StockCountScreenActions(
            onCreateSession = { productId, note ->
                stockCountViewModel.createSessionForProduct(productId, note)
                stockCountState = stockCountViewModel.state
            },
            onBlindCountQuantityChange = { value ->
                stockCountViewModel.updateBlindCountQuantity(value)
                stockCountState = stockCountViewModel.state
            },
            onBlindCountNoteChange = { value ->
                stockCountViewModel.updateBlindCountNote(value)
                stockCountState = stockCountViewModel.state
            },
            onReviewNoteChange = { value ->
                stockCountViewModel.updateReviewNote(value)
                stockCountState = stockCountViewModel.state
            },
            onRecordBlindCount = {
                stockCountViewModel.recordBlindCountForActiveSession()
                stockCountState = stockCountViewModel.state
            },
            onApproveSession = {
                stockCountViewModel.approveActiveSession()
                stockCountState = stockCountViewModel.state
            },
            onCancelSession = {
                stockCountViewModel.cancelActiveSession()
                stockCountState = stockCountViewModel.state
            },
        )
    }
    val restockActions = remember(restockViewModel) {
        RestockScreenActions(
            onRefreshBoard = {
                restockViewModel.refreshBoard()
                restockState = restockViewModel.state
            },
            onSelectReplenishmentProduct = { productId ->
                restockViewModel.selectReplenishmentProduct(productId)
                restockState = restockViewModel.state
            },
            onRequestedQuantityChange = { value ->
                restockViewModel.updateRequestedQuantity(value)
                restockState = restockViewModel.state
            },
            onPickedQuantityChange = { value ->
                restockViewModel.updatePickedQuantity(value)
                restockState = restockViewModel.state
            },
            onNoteChange = { value ->
                restockViewModel.updateNote(value)
                restockState = restockViewModel.state
            },
            onCompletionNoteChange = { value ->
                restockViewModel.updateCompletionNote(value)
                restockState = restockViewModel.state
            },
            onSourcePostureChange = { value ->
                restockViewModel.updateSourcePosture(value)
                restockState = restockViewModel.state
            },
            onCreateTask = {
                restockViewModel.createRestockTaskForCurrentProduct()
                restockState = restockViewModel.state
            },
            onPickTask = {
                restockViewModel.pickActiveTaskForCurrentProduct()
                restockState = restockViewModel.state
            },
            onCompleteTask = {
                restockViewModel.completeActiveTaskForCurrentProduct()
                restockState = restockViewModel.state
            },
            onCancelTask = {
                restockViewModel.cancelActiveTaskForCurrentProduct()
                restockState = restockViewModel.state
            },
        )
    }
    val expiryActions = remember(expiryViewModel) {
        ExpiryScreenActions(
            onCreateSession = { batchLotId, note ->
                expiryViewModel.createSessionForBatch(batchLotId, note)
                expiryState = expiryViewModel.state
            },
            onProposedQuantityChange = { value ->
                expiryViewModel.updateProposedQuantity(value)
                expiryState = expiryViewModel.state
            },
            onWriteOffReasonChange = { value ->
                expiryViewModel.updateWriteOffReason(value)
                expiryState = expiryViewModel.state
            },
            onSessionNoteChange = { value ->
                expiryViewModel.updateSessionNote(value)
                expiryState = expiryViewModel.state
            },
            onReviewNoteChange = { value ->
                expiryViewModel.updateReviewNote(value)
                expiryState = expiryViewModel.state
            },
            onRecordReview = {
                expiryViewModel.recordReviewForActiveSession()
                expiryState = expiryViewModel.state
            },
            onApproveSession = {
                expiryViewModel.approveActiveSession()
                expiryState = expiryViewModel.state
            },
            onCancelSession = {
                expiryViewModel.cancelActiveSession()
                expiryState = expiryViewModel.state
            },
        )
    }

    DisposableEffect(application, pairingState.pairedDevice?.deviceId, handheldSection, tabletSection) {
        val mobileApp = application
        if (mobileApp == null || pairingState.pairedDevice == null) {
            onDispose { }
        } else {
            val removeListener = mobileApp.addExternalBarcodeListener { barcode ->
                val shellMode = resolveStoreMobileShellMode(pairingState.pairedDevice?.runtimeProfile)
                val isScanSectionActive = if (shellMode == StoreMobileShellMode.TABLET) {
                    tabletSection == MobileOperationsSection.SCAN
                } else {
                    handheldSection == MobileOperationsSection.SCAN
                }
                when (barcode) {
                    is ExternalScannerEvent.BarcodeDetected -> {
                        if (!isScanSectionActive) {
                            return@addExternalBarcodeListener
                        }
                        scanLookupViewModel.onExternalScannerDetected(
                            rawBarcode = barcode.barcode,
                            detectedAtMillis = barcode.detectedAtMillis,
                        )
                        scanLookupState = scanLookupViewModel.state
                    }

                    is ExternalScannerEvent.PayloadError -> {
                        scanLookupViewModel.reportExternalScannerPayloadError(
                            message = barcode.message,
                            detectedAtMillis = barcode.detectedAtMillis,
                        )
                        scanLookupState = scanLookupViewModel.state
                    }
                }
            }
            onDispose { removeListener() }
        }
    }

    DisposableEffect(application) {
        val mobileApp = application
        if (mobileApp == null) {
            onDispose { }
        } else {
            val removeAvailabilityListener = mobileApp.addZebraAvailabilityListener { isAvailable ->
                scanLookupViewModel.updateZebraDataWedgeAvailability(isAvailable)
                scanLookupState = scanLookupViewModel.state
            }
            val removeResultListener = mobileApp.addZebraResultListener { result ->
                scanLookupViewModel.applyZebraDataWedgeResult(result)
                scanLookupState = scanLookupViewModel.state
            }
            onDispose {
                removeAvailabilityListener()
                removeResultListener()
            }
        }
    }

    LaunchedEffect(scanLookupState.externalScannerStatus, scanLookupState.lastExternalScanAt) {
        if (scanLookupState.externalScannerStatus == com.store.mobile.ui.scan.ScanExternalScannerStatus.RECENT_SCAN) {
            kotlinx.coroutines.delay(5 * 60 * 1000L + 1_000L)
            scanLookupViewModel.refreshExternalScannerStatus(System.currentTimeMillis())
            scanLookupState = scanLookupViewModel.state
        }
    }

    LaunchedEffect(currentSession?.expiresAt, pairingState.sessionStatus) {
        if (currentSession == null || pairingState.sessionStatus != PairingSessionStatus.ACTIVE) {
            return@LaunchedEffect
        }
        val expiresAtMillis = parseStoreMobileExpiryMillis(currentSession.expiresAt)
            ?: return@LaunchedEffect
        val delayMillis = expiresAtMillis - System.currentTimeMillis()
        if (delayMillis <= 0) {
            pairingViewModel.handleExpiredSession()
            pairingState = pairingViewModel.state
            return@LaunchedEffect
        }
        kotlinx.coroutines.delay(delayMillis + 1_000L)
        pairingViewModel.handleExpiredSession()
        pairingState = pairingViewModel.state
    }

    LaunchedEffect(pairingState.pairedDevice?.deviceId, operationsBranchId, stockCountViewModel) {
        if (pairingState.pairedDevice == null || operationsBranchId == null) {
            receivingViewModel.clearBranch()
            stockCountViewModel.clearBranch()
            restockViewModel.clearBranch()
            expiryViewModel.clearBranch()
        } else {
            receivingViewModel.loadBranch(branchId = operationsBranchId)
            stockCountViewModel.loadBranch(branchId = operationsBranchId)
            restockViewModel.loadBranch(branchId = operationsBranchId)
            expiryViewModel.loadBranch(branchId = operationsBranchId)
        }
        receivingState = receivingViewModel.state
        stockCountState = stockCountViewModel.state
        restockState = restockViewModel.state
        expiryState = expiryViewModel.state
    }

    LaunchedEffect(
        scanLookupState.productId,
        scanLookupState.productName,
        scanLookupState.skuCode,
        scanLookupState.barcode,
        scanLookupState.stockOnHand,
        scanLookupState.reorderPoint,
        scanLookupState.targetStock,
    ) {
        restockViewModel.syncScannedLookup(scanLookupState)
        restockState = restockViewModel.state
    }

    StoreMobileTheme(themeMode = StoreMobileAppBootstrap.defaultThemeMode) {
        Surface(modifier = Modifier.fillMaxSize()) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(24.dp),
                verticalArrangement = Arrangement.Top,
            ) {
                if (!hasActiveRuntimeSession) {
                    StoreMobileEntrySurface(
                        state = pairingState,
                        onHubBaseUrlChange = { hubBaseUrl ->
                            pairingViewModel.updateManualActivation(
                                hubBaseUrl = hubBaseUrl,
                                activationCode = pairingState.activationCode,
                            )
                            pairingState = pairingViewModel.state
                        },
                        onActivationCodeChange = { activationCode ->
                            pairingViewModel.updateManualActivation(
                                hubBaseUrl = pairingState.hubBaseUrl,
                                activationCode = activationCode,
                            )
                            pairingState = pairingViewModel.state
                        },
                        onRequestedSessionSurfaceChange = { requestedSessionSurface ->
                            pairingViewModel.updateRequestedSessionSurface(requestedSessionSurface)
                            pairingState = pairingViewModel.state
                        },
                        onRedeemActivation = {
                            pairingViewModel.redeemManualActivation(
                                installationId = "android-installation-demo",
                            )
                            pairingState = pairingViewModel.state
                        },
                        onUnpairDevice = {
                            pairingViewModel.unpairDevice()
                            pairingState = pairingViewModel.state
                        },
                    )
                } else {
                    val shellMode = resolveStoreMobileShellMode(pairingState.pairedDevice?.runtimeProfile)
                    val runtimeStatusState = buildRuntimeStatusState(
                        connected = hasActiveRuntimeSession,
                        pendingSyncCount = 0,
                        deviceId = pairingState.pairedDevice?.deviceId,
                        hubBaseUrl = pairingState.pairedDevice?.hubBaseUrl,
                        sessionExpiresAt = currentSession?.expiresAt,
                        externalScannerStatus = scanLookupState.externalScannerStatus,
                        lastExternalScanAt = scanLookupState.lastExternalScanAt,
                        externalScannerMessage = scanLookupState.externalScannerMessage,
                        zebraDataWedgeStatus = scanLookupState.zebraDataWedgeStatus,
                        zebraDataWedgeMessage = scanLookupState.zebraDataWedgeMessage,
                    )

                    if (shellMode == StoreMobileShellMode.TABLET) {
                        InventoryTabletShell(
                            activeSection = tabletSection,
                            onSelectSection = { section -> tabletSection = section },
                            scanLookupState = scanLookupState,
                            onDraftBarcodeChange = { barcode ->
                                scanLookupViewModel.updateDraftBarcode(barcode)
                                scanLookupState = scanLookupViewModel.state
                            },
                            onLookupBarcode = {
                                scanLookupViewModel.lookupDraftBarcode()
                                scanLookupState = scanLookupViewModel.state
                            },
                            onConfigureZebraDataWedge = {
                                scanLookupViewModel.beginZebraDataWedgeProvisioning()
                                scanLookupState = scanLookupViewModel.state
                                if (activity == null) {
                                    scanLookupViewModel.applyZebraDataWedgeResult(
                                        ZebraDataWedgeResult.Error("Zebra setup host is unavailable."),
                                    )
                                    scanLookupState = scanLookupViewModel.state
                                } else {
                                    activity.configureZebraDataWedge()
                                }
                            },
                            onCameraPermissionResolved = { granted ->
                                scanLookupViewModel.setCameraPermission(granted)
                                scanLookupState = scanLookupViewModel.state
                            },
                            onCameraPreviewFailure = { message ->
                                scanLookupViewModel.reportCameraUnavailable(message)
                                scanLookupState = scanLookupViewModel.state
                            },
                            onCameraBarcodeDetected = { barcode ->
                                scanLookupViewModel.onCameraBarcodeDetected(
                                    rawBarcode = barcode,
                                    detectedAtMillis = System.currentTimeMillis(),
                                )
                                scanLookupState = scanLookupViewModel.state
                            },
                            receivingState = receivingState,
                            receivingActions = receivingActions,
                            stockCountState = stockCountState,
                            stockCountActions = stockCountActions,
                            restockState = restockState,
                            restockActions = restockActions,
                            expiryState = expiryState,
                            expiryActions = expiryActions,
                            runtimeStatusState = runtimeStatusState,
                            onSignOut = {
                                pairingViewModel.signOutSession()
                                pairingState = pairingViewModel.state
                            },
                            onUnpair = {
                                pairingViewModel.unpairDevice()
                                pairingState = pairingViewModel.state
                            },
                        )
                    } else {
                        HandheldStoreShell(
                            activeSection = handheldSection,
                            onSelectSection = { section -> handheldSection = section },
                            scanLookupState = scanLookupState,
                            onDraftBarcodeChange = { barcode ->
                                scanLookupViewModel.updateDraftBarcode(barcode)
                                scanLookupState = scanLookupViewModel.state
                            },
                            onLookupBarcode = {
                                scanLookupViewModel.lookupDraftBarcode()
                                scanLookupState = scanLookupViewModel.state
                            },
                            onConfigureZebraDataWedge = {
                                scanLookupViewModel.beginZebraDataWedgeProvisioning()
                                scanLookupState = scanLookupViewModel.state
                                if (activity == null) {
                                    scanLookupViewModel.applyZebraDataWedgeResult(
                                        ZebraDataWedgeResult.Error("Zebra setup host is unavailable."),
                                    )
                                    scanLookupState = scanLookupViewModel.state
                                } else {
                                    activity.configureZebraDataWedge()
                                }
                            },
                            onCameraPermissionResolved = { granted ->
                                scanLookupViewModel.setCameraPermission(granted)
                                scanLookupState = scanLookupViewModel.state
                            },
                            onCameraPreviewFailure = { message ->
                                scanLookupViewModel.reportCameraUnavailable(message)
                                scanLookupState = scanLookupViewModel.state
                            },
                            onCameraBarcodeDetected = { barcode ->
                                scanLookupViewModel.onCameraBarcodeDetected(
                                    rawBarcode = barcode,
                                    detectedAtMillis = System.currentTimeMillis(),
                                )
                                scanLookupState = scanLookupViewModel.state
                            },
                            receivingState = receivingState,
                            receivingActions = receivingActions,
                            stockCountState = stockCountState,
                            stockCountActions = stockCountActions,
                            restockState = restockState,
                            restockActions = restockActions,
                            expiryState = expiryState,
                            expiryActions = expiryActions,
                            runtimeStatusState = runtimeStatusState,
                            onSignOut = {
                                pairingViewModel.signOutSession()
                                pairingState = pairingViewModel.state
                            },
                            onUnpair = {
                                pairingViewModel.unpairDevice()
                                pairingState = pairingViewModel.state
                            },
                        )
                    }
                }
            }
        }
    }
}
