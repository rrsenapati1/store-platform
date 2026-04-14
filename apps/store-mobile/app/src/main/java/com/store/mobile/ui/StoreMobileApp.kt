package com.store.mobile.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.store.mobile.operations.InMemoryExpiryRepository
import com.store.mobile.operations.InMemoryReceivingRepository
import com.store.mobile.operations.InMemoryStockCountRepository
import com.store.mobile.runtime.FakeStoreMobileHubClient
import com.store.mobile.runtime.InMemoryStoreMobilePairingRepository
import com.store.mobile.runtime.InMemoryStoreMobileSessionRepository
import com.store.mobile.runtime.StoreMobilePairingRepository
import com.store.mobile.runtime.StoreMobileSessionRepository
import com.store.mobile.ui.operations.ExpiryScreen
import com.store.mobile.ui.operations.MobileOperationsSection
import com.store.mobile.ui.operations.OperationsHomeScreen
import com.store.mobile.ui.operations.ReceivingScreen
import com.store.mobile.ui.operations.StockCountScreen
import com.store.mobile.ui.pairing.PairingScreen
import com.store.mobile.ui.pairing.PairingViewModel
import com.store.mobile.scan.InMemoryScanLookupRepository
import com.store.mobile.ui.runtime.RuntimeStatusScreen
import com.store.mobile.ui.runtime.buildRuntimeStatusState
import com.store.mobile.ui.scan.ScanLookupScreen
import com.store.mobile.ui.scan.ScanLookupViewModel

@Composable
fun StoreMobileApp() {
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
    var scanDraftBarcode by remember { mutableStateOf("") }
    var scanLookupState by remember { mutableStateOf(scanLookupViewModel.state) }
    var activeSection by remember { mutableStateOf(MobileOperationsSection.SCAN) }

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
                        onRedeemActivation = {
                            pairingViewModel.redeemManualActivation(
                                installationId = "android-installation-demo",
                            )
                            pairingState = pairingViewModel.state
                        },
                    )
                } else {
                    val runtimeStatusState = buildRuntimeStatusState(
                        connected = true,
                        pendingSyncCount = 0,
                        deviceId = pairingState.pairedDevice?.deviceId,
                        hubBaseUrl = pairingState.pairedDevice?.hubBaseUrl,
                        sessionExpiresAt = sessionRepository.loadSession()?.expiresAt,
                    )
                    OperationsHomeScreen(
                        activeSection = activeSection,
                        onSelectSection = { section -> activeSection = section },
                    )
                    when (activeSection) {
                        MobileOperationsSection.SCAN -> {
                            ScanLookupScreen(
                                draftBarcode = scanDraftBarcode,
                                state = scanLookupState,
                                onDraftBarcodeChange = { barcode -> scanDraftBarcode = barcode },
                                onLookupBarcode = {
                                    scanLookupViewModel.lookupScannedBarcode(scanDraftBarcode)
                                    scanLookupState = scanLookupViewModel.state
                                },
                            )
                        }

                        MobileOperationsSection.RECEIVING -> {
                            ReceivingScreen(board = receivingRepository.loadReceivingBoard(branchId = "branch-demo-1"))
                        }

                        MobileOperationsSection.STOCK_COUNT -> {
                            StockCountScreen(context = stockCountRepository.loadStockCountContext(branchId = "branch-demo-1"))
                        }

                        MobileOperationsSection.EXPIRY -> {
                            ExpiryScreen(report = expiryRepository.loadExpiryReport(branchId = "branch-demo-1"))
                        }

                        MobileOperationsSection.RUNTIME -> {
                            RuntimeStatusScreen(state = runtimeStatusState)
                        }
                    }
                }
            }
        }
    }
}
