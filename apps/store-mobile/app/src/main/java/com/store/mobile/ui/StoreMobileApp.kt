package com.store.mobile.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.store.mobile.StoreMobileApplication
import com.store.mobile.operations.InMemoryExpiryRepository
import com.store.mobile.operations.InMemoryReceivingRepository
import com.store.mobile.operations.InMemoryStockCountRepository
import com.store.mobile.runtime.FakeStoreMobileHubClient
import com.store.mobile.runtime.InMemoryStoreMobilePairingRepository
import com.store.mobile.runtime.InMemoryStoreMobileSessionRepository
import com.store.mobile.runtime.StoreMobilePairingRepository
import com.store.mobile.runtime.StoreMobileSessionRepository
import com.store.mobile.scan.ExternalScannerEvent
import com.store.mobile.scan.InMemoryScanLookupRepository
import com.store.mobile.ui.handheld.HandheldStoreShell
import com.store.mobile.ui.operations.MobileOperationsSection
import com.store.mobile.ui.pairing.PairingScreen
import com.store.mobile.ui.pairing.PairingViewModel
import com.store.mobile.ui.runtime.buildRuntimeStatusState
import com.store.mobile.ui.scan.ScanLookupViewModel
import com.store.mobile.ui.tablet.InventoryTabletShell

@Composable
fun StoreMobileApp() {
    val context = LocalContext.current
    val application = remember(context) { context.applicationContext as? StoreMobileApplication }
    val pairingRepository: StoreMobilePairingRepository = remember { InMemoryStoreMobilePairingRepository() }
    val sessionRepository: StoreMobileSessionRepository = remember { InMemoryStoreMobileSessionRepository() }
    val pairingViewModel = remember {
        PairingViewModel(
            pairingRepository = pairingRepository,
            sessionRepository = sessionRepository,
            hubClient = FakeStoreMobileHubClient(),
        )
    }
    val scanLookupViewModel = remember {
        ScanLookupViewModel(repository = InMemoryScanLookupRepository())
    }
    val receivingRepository = remember { InMemoryReceivingRepository() }
    val stockCountRepository = remember { InMemoryStockCountRepository() }
    val expiryRepository = remember { InMemoryExpiryRepository() }
    var pairingState by remember { mutableStateOf(pairingViewModel.state) }
    var scanLookupState by remember { mutableStateOf(scanLookupViewModel.state) }
    var handheldSection by remember { mutableStateOf(MobileOperationsSection.SCAN) }
    var tabletSection by remember { mutableStateOf(MobileOperationsSection.RECEIVING) }

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

    LaunchedEffect(scanLookupState.externalScannerStatus, scanLookupState.lastExternalScanAt) {
        if (scanLookupState.externalScannerStatus == com.store.mobile.ui.scan.ScanExternalScannerStatus.RECENT_SCAN) {
            kotlinx.coroutines.delay(5 * 60 * 1000L + 1_000L)
            scanLookupViewModel.refreshExternalScannerStatus(System.currentTimeMillis())
            scanLookupState = scanLookupViewModel.state
        }
    }

    MaterialTheme {
        Surface(modifier = Modifier.fillMaxSize()) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(24.dp),
                verticalArrangement = Arrangement.Top,
                horizontalAlignment = Alignment.Start,
            ) {
                if (pairingState.pairedDevice == null) {
                    PairingScreen(
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
                    )
                } else {
                    val shellMode = resolveStoreMobileShellMode(pairingState.pairedDevice?.runtimeProfile)
                    val receivingBoard = receivingRepository.loadReceivingBoard(branchId = "branch-demo-1")
                    val stockCountContext = stockCountRepository.loadStockCountContext(branchId = "branch-demo-1")
                    val expiryReport = expiryRepository.loadExpiryReport(branchId = "branch-demo-1")
                    val runtimeStatusState = buildRuntimeStatusState(
                        connected = true,
                        pendingSyncCount = 0,
                        deviceId = pairingState.pairedDevice?.deviceId,
                        hubBaseUrl = pairingState.pairedDevice?.hubBaseUrl,
                        sessionExpiresAt = sessionRepository.loadSession()?.expiresAt,
                        externalScannerStatus = scanLookupState.externalScannerStatus,
                        lastExternalScanAt = scanLookupState.lastExternalScanAt,
                        externalScannerMessage = scanLookupState.externalScannerMessage,
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
                            receivingBoard = receivingBoard,
                            stockCountContext = stockCountContext,
                            expiryReport = expiryReport,
                            runtimeStatusState = runtimeStatusState,
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
                            receivingBoard = receivingBoard,
                            stockCountContext = stockCountContext,
                            expiryReport = expiryReport,
                            runtimeStatusState = runtimeStatusState,
                        )
                    }
                }
            }
        }
    }
}
