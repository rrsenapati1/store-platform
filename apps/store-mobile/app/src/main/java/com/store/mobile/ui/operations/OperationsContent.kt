package com.store.mobile.ui.operations

import androidx.compose.runtime.Composable
import com.store.mobile.operations.ExpiryReport
import com.store.mobile.operations.ReceivingBoard
import com.store.mobile.operations.StockCountContext
import com.store.mobile.ui.runtime.RuntimeStatusScreen
import com.store.mobile.ui.runtime.RuntimeStatusUiState
import com.store.mobile.ui.scan.ScanLookupScreen
import com.store.mobile.ui.scan.ScanLookupUiState

fun mobileOperationsSectionLabel(section: MobileOperationsSection): String {
    return when (section) {
        MobileOperationsSection.SCAN -> "Scan"
        MobileOperationsSection.RECEIVING -> "Receiving"
        MobileOperationsSection.STOCK_COUNT -> "Count"
        MobileOperationsSection.EXPIRY -> "Expiry"
        MobileOperationsSection.RUNTIME -> "Status"
    }
}

@Composable
fun MobileOperationsContent(
    activeSection: MobileOperationsSection,
    draftBarcode: String,
    scanLookupState: ScanLookupUiState,
    onDraftBarcodeChange: (String) -> Unit,
    onLookupBarcode: () -> Unit,
    receivingBoard: ReceivingBoard,
    stockCountContext: StockCountContext,
    expiryReport: ExpiryReport,
    runtimeStatusState: RuntimeStatusUiState,
) {
    when (activeSection) {
        MobileOperationsSection.SCAN -> {
            ScanLookupScreen(
                draftBarcode = draftBarcode,
                state = scanLookupState,
                onDraftBarcodeChange = onDraftBarcodeChange,
                onLookupBarcode = onLookupBarcode,
            )
        }

        MobileOperationsSection.RECEIVING -> ReceivingScreen(board = receivingBoard)
        MobileOperationsSection.STOCK_COUNT -> StockCountScreen(context = stockCountContext)
        MobileOperationsSection.EXPIRY -> ExpiryScreen(report = expiryReport)
        MobileOperationsSection.RUNTIME -> RuntimeStatusScreen(state = runtimeStatusState)
    }
}
