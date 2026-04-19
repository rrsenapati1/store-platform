package com.store.mobile.ui.handheld

import androidx.compose.runtime.Composable
import com.store.mobile.ui.operations.MobileOperationsSection
import com.store.mobile.ui.operations.ExpiryScreenActions
import com.store.mobile.ui.operations.ExpiryUiState
import com.store.mobile.ui.operations.ReceivingScreenActions
import com.store.mobile.ui.operations.ReceivingUiState
import com.store.mobile.ui.operations.RestockScreenActions
import com.store.mobile.ui.operations.RestockUiState
import com.store.mobile.ui.operations.StockCountScreenActions
import com.store.mobile.ui.operations.StockCountUiState
import com.store.mobile.ui.runtime.RuntimeStatusUiState
import com.store.mobile.ui.scan.ScanLookupUiState

@Composable
fun HandheldStoreShell(
    activeSection: MobileOperationsSection,
    onSelectSection: (MobileOperationsSection) -> Unit,
    scanLookupState: ScanLookupUiState,
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
    onSignOut: () -> Unit,
    onUnpair: () -> Unit,
) {
    HandheldRuntimeShell(
        activeSection = activeSection,
        onSelectSection = onSelectSection,
        scanLookupState = scanLookupState,
        onDraftBarcodeChange = onDraftBarcodeChange,
        onLookupBarcode = onLookupBarcode,
        onConfigureZebraDataWedge = onConfigureZebraDataWedge,
        onCameraPermissionResolved = onCameraPermissionResolved,
        onCameraPreviewFailure = onCameraPreviewFailure,
        onCameraBarcodeDetected = onCameraBarcodeDetected,
        receivingState = receivingState,
        receivingActions = receivingActions,
        stockCountState = stockCountState,
        stockCountActions = stockCountActions,
        restockState = restockState,
        restockActions = restockActions,
        expiryState = expiryState,
        expiryActions = expiryActions,
        runtimeStatusState = runtimeStatusState,
        onSignOut = onSignOut,
        onUnpair = onUnpair,
    )
}
