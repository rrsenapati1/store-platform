package com.store.mobile.ui.operations

import androidx.compose.runtime.Composable
import com.store.mobile.ui.runtime.RuntimeStatusScreen
import com.store.mobile.ui.runtime.RuntimeStatusUiState
import com.store.mobile.ui.scan.ScanLookupScreen
import com.store.mobile.ui.scan.ScanLookupUiState

fun mobileOperationsSectionLabel(section: MobileOperationsSection): String {
    return when (section) {
        MobileOperationsSection.SCAN -> "Scan"
        MobileOperationsSection.RESTOCK -> "Restock"
        MobileOperationsSection.RECEIVING -> "Receiving"
        MobileOperationsSection.STOCK_COUNT -> "Count"
        MobileOperationsSection.EXPIRY -> "Expiry"
        MobileOperationsSection.RUNTIME -> "Status"
    }
}

@Composable
fun MobileOperationsContent(
    activeSection: MobileOperationsSection,
    scanLookupState: ScanLookupUiState,
    isTabletLayout: Boolean,
    onDraftBarcodeChange: (String) -> Unit,
    onLookupBarcode: () -> Unit,
    onConfigureZebraDataWedge: () -> Unit,
    onCameraPermissionResolved: (Boolean) -> Unit,
    onCameraPreviewFailure: (String) -> Unit,
    onCameraBarcodeDetected: (String) -> Unit,
    receivingState: ReceivingUiState,
    receivingActions: ReceivingScreenActions,
    stockCountState: StockCountUiState,
    stockCountActions: StockCountScreenActions,
    restockState: RestockUiState,
    restockActions: RestockScreenActions,
    expiryState: ExpiryUiState,
    expiryActions: ExpiryScreenActions,
    runtimeStatusState: RuntimeStatusUiState,
    onSelectTaskSection: (MobileOperationsSection) -> Unit = {},
    onSignOut: () -> Unit = {},
    onUnpair: () -> Unit = {},
) {
    when (activeSection) {
        MobileOperationsSection.SCAN -> {
            ScanLookupScreen(
                state = scanLookupState,
                isTabletLayout = isTabletLayout,
                onDraftBarcodeChange = onDraftBarcodeChange,
                onLookupBarcode = onLookupBarcode,
                onConfigureZebraDataWedge = onConfigureZebraDataWedge,
                onCameraPermissionResolved = onCameraPermissionResolved,
                onCameraPreviewFailure = onCameraPreviewFailure,
                onCameraBarcodeDetected = onCameraBarcodeDetected,
                receivingState = receivingState,
                stockCountState = stockCountState,
                restockState = restockState,
                expiryState = expiryState,
                onSelectTaskSection = onSelectTaskSection,
            )
        }

        MobileOperationsSection.RESTOCK -> RestockScreen(
            state = restockState,
            isTabletLayout = isTabletLayout,
            actions = restockActions,
        )
        MobileOperationsSection.RECEIVING -> ReceivingScreen(
            state = receivingState,
            actions = receivingActions,
        )
        MobileOperationsSection.STOCK_COUNT -> StockCountScreen(
            state = stockCountState,
            actions = stockCountActions,
        )
        MobileOperationsSection.EXPIRY -> ExpiryScreen(
            state = expiryState,
            actions = expiryActions,
        )
        MobileOperationsSection.RUNTIME -> RuntimeStatusScreen(
            state = runtimeStatusState,
            onSignOut = onSignOut,
            onUnpair = onUnpair,
        )
    }
}
