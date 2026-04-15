package com.store.mobile.ui.handheld

import androidx.compose.runtime.Composable
import com.store.mobile.operations.ExpiryReport
import com.store.mobile.operations.ReceivingBoard
import com.store.mobile.operations.StockCountContext
import com.store.mobile.ui.operations.MobileOperationsContent
import com.store.mobile.ui.operations.MobileOperationsSection
import com.store.mobile.ui.operations.OperationsHomeScreen
import com.store.mobile.ui.runtime.RuntimeStatusUiState
import com.store.mobile.ui.scan.ScanLookupUiState

@Composable
fun HandheldStoreShell(
    activeSection: MobileOperationsSection,
    onSelectSection: (MobileOperationsSection) -> Unit,
    scanLookupState: ScanLookupUiState,
    onDraftBarcodeChange: (String) -> Unit,
    onLookupBarcode: () -> Unit,
    onCameraPermissionResolved: (Boolean) -> Unit,
    onCameraPreviewFailure: (String) -> Unit,
    onCameraBarcodeDetected: (String) -> Unit,
    receivingBoard: ReceivingBoard,
    stockCountContext: StockCountContext,
    expiryReport: ExpiryReport,
    runtimeStatusState: RuntimeStatusUiState,
) {
    OperationsHomeScreen(
        activeSection = activeSection,
        onSelectSection = onSelectSection,
    )
    MobileOperationsContent(
        activeSection = activeSection,
        scanLookupState = scanLookupState,
        isTabletLayout = false,
        onDraftBarcodeChange = onDraftBarcodeChange,
        onLookupBarcode = onLookupBarcode,
        onCameraPermissionResolved = onCameraPermissionResolved,
        onCameraPreviewFailure = onCameraPreviewFailure,
        onCameraBarcodeDetected = onCameraBarcodeDetected,
        receivingBoard = receivingBoard,
        stockCountContext = stockCountContext,
        expiryReport = expiryReport,
        runtimeStatusState = runtimeStatusState,
    )
}
