package com.store.mobile.ui.handheld

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.store.mobile.ui.operations.ExpiryScreenActions
import com.store.mobile.ui.operations.ExpiryUiState
import com.store.mobile.ui.operations.MobileOperationsContent
import com.store.mobile.ui.operations.MobileOperationsSection
import com.store.mobile.ui.operations.ReceivingScreenActions
import com.store.mobile.ui.operations.ReceivingUiState
import com.store.mobile.ui.operations.RestockScreenActions
import com.store.mobile.ui.operations.RestockUiState
import com.store.mobile.ui.operations.StockCountScreenActions
import com.store.mobile.ui.operations.StockCountUiState
import com.store.mobile.ui.runtime.RuntimeStatusUiState
import com.store.mobile.ui.scan.ScanLookupUiState

private val handheldTaskSections = listOf(
    MobileOperationsSection.RECEIVING,
    MobileOperationsSection.STOCK_COUNT,
    MobileOperationsSection.RESTOCK,
    MobileOperationsSection.EXPIRY,
)

@Composable
fun HandheldTasksScreen(
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
    val postureModel = buildHandheldTaskPostureModel(
        receivingState = receivingState,
        stockCountState = stockCountState,
        restockState = restockState,
        expiryState = expiryState,
    )

    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(18.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Text(
                    text = postureModel.eyebrow,
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary,
                )
                Text(
                    text = postureModel.title,
                    style = MaterialTheme.typography.titleMedium,
                )
                Text(
                    text = postureModel.detail,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        Card(modifier = Modifier.fillMaxWidth()) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(18.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Text(
                    text = "Task sections",
                    style = MaterialTheme.typography.titleMedium,
                )
                Text(
                    text = "Receiving, count, restock, and expiry work stay here so scan remains the primary home for new item-driven actions.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                handheldTaskSections.forEach { section ->
                    if (section == activeSection) {
                        Button(
                            onClick = { onSelectSection(section) },
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Text(text = taskSectionLabel(section))
                        }
                    } else {
                        OutlinedButton(
                            onClick = { onSelectSection(section) },
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Text(text = taskSectionLabel(section))
                        }
                    }
                }
            }
        }

        MobileOperationsContent(
            activeSection = activeSection,
            scanLookupState = scanLookupState,
            isTabletLayout = false,
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
            onSelectTaskSection = onSelectSection,
        )
    }
}

private fun taskSectionLabel(section: MobileOperationsSection): String {
    return when (section) {
        MobileOperationsSection.RECEIVING -> "Receiving"
        MobileOperationsSection.STOCK_COUNT -> "Count"
        MobileOperationsSection.RESTOCK -> "Restock"
        MobileOperationsSection.EXPIRY -> "Expiry"
        else -> section.name
    }
}
