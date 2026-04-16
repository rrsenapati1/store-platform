package com.store.mobile.ui.tablet

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.store.mobile.ui.operations.MobileOperationsContent
import com.store.mobile.ui.operations.MobileOperationsSection
import com.store.mobile.ui.operations.ExpiryScreenActions
import com.store.mobile.ui.operations.ExpiryUiState
import com.store.mobile.ui.operations.ReceivingScreenActions
import com.store.mobile.ui.operations.ReceivingUiState
import com.store.mobile.ui.operations.RestockScreenActions
import com.store.mobile.ui.operations.RestockUiState
import com.store.mobile.ui.operations.StockCountScreenActions
import com.store.mobile.ui.operations.StockCountUiState
import com.store.mobile.ui.operations.mobileOperationsSectionLabel
import com.store.mobile.ui.runtime.RuntimeStatusUiState
import com.store.mobile.ui.scan.ScanLookupUiState

@Composable
fun InventoryTabletShell(
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
) {
    Row(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 24.dp),
        horizontalArrangement = Arrangement.spacedBy(24.dp),
    ) {
        Column(
            modifier = Modifier.weight(0.32f),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text(text = "Inventory tablet", style = MaterialTheme.typography.headlineSmall)
            Text(
                text = "Backroom-first runtime for receiving, stock counts, expiry review, and branch posture.",
                style = MaterialTheme.typography.bodyMedium,
            )
            listOf(
                MobileOperationsSection.RECEIVING,
                MobileOperationsSection.STOCK_COUNT,
                MobileOperationsSection.EXPIRY,
                MobileOperationsSection.SCAN,
                MobileOperationsSection.RESTOCK,
                MobileOperationsSection.RUNTIME,
            ).forEach { section ->
                Button(
                    onClick = { onSelectSection(section) },
                    enabled = section != activeSection,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(text = mobileOperationsSectionLabel(section))
                }
            }
        }
        Column(modifier = Modifier.weight(0.68f)) {
            MobileOperationsContent(
                activeSection = activeSection,
                scanLookupState = scanLookupState,
                isTabletLayout = true,
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
            )
        }
    }
}
