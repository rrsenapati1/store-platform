package com.store.mobile.ui.handheld

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.store.mobile.ui.operations.ExpiryScreenActions
import com.store.mobile.ui.operations.ExpiryUiState
import com.store.mobile.ui.operations.MobileOperationsSection
import com.store.mobile.ui.operations.ReceivingScreenActions
import com.store.mobile.ui.operations.ReceivingUiState
import com.store.mobile.ui.operations.RestockScreenActions
import com.store.mobile.ui.operations.RestockUiState
import com.store.mobile.ui.operations.StockCountScreenActions
import com.store.mobile.ui.operations.StockCountUiState
import com.store.mobile.ui.runtime.RuntimeStatusScreen
import com.store.mobile.ui.runtime.RuntimeStatusUiState
import com.store.mobile.ui.scan.ScanLookupScreen
import com.store.mobile.ui.scan.ScanLookupUiState

@Composable
fun HandheldRuntimeShell(
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
    val destination = resolveHandheldRuntimeDestination(activeSection)
    val taskSection = resolveHandheldTaskSection(activeSection)

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        HandheldRuntimeSummary(state = runtimeStatusState)
        Text(
            text = "Handheld associate runtime",
            style = MaterialTheme.typography.headlineSmall,
        )
        DestinationButtonRow(
            destination = destination,
            onSelectDestination = { next ->
                when (next) {
                    HandheldRuntimeDestination.SCAN -> onSelectSection(MobileOperationsSection.SCAN)
                    HandheldRuntimeDestination.TASKS -> onSelectSection(taskSection)
                    HandheldRuntimeDestination.RUNTIME -> onSelectSection(MobileOperationsSection.RUNTIME)
                }
            },
        )
        when (destination) {
            HandheldRuntimeDestination.SCAN -> ScanLookupScreen(
                state = scanLookupState,
                isTabletLayout = false,
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
                onSelectTaskSection = onSelectSection,
            )

            HandheldRuntimeDestination.TASKS -> HandheldTasksScreen(
                activeSection = taskSection,
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
            )

            HandheldRuntimeDestination.RUNTIME -> RuntimeStatusScreen(
                state = runtimeStatusState,
                onSignOut = onSignOut,
                onUnpair = onUnpair,
            )
        }
    }
}

@Composable
private fun DestinationButtonRow(
    destination: HandheldRuntimeDestination,
    onSelectDestination: (HandheldRuntimeDestination) -> Unit,
) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        destinationButton(
            destination = HandheldRuntimeDestination.SCAN,
            current = destination,
            label = "Scan",
            onSelectDestination = onSelectDestination,
        )
        destinationButton(
            destination = HandheldRuntimeDestination.TASKS,
            current = destination,
            label = "Tasks",
            onSelectDestination = onSelectDestination,
        )
        destinationButton(
            destination = HandheldRuntimeDestination.RUNTIME,
            current = destination,
            label = "Runtime",
            onSelectDestination = onSelectDestination,
        )
    }
}

@Composable
private fun destinationButton(
    destination: HandheldRuntimeDestination,
    current: HandheldRuntimeDestination,
    label: String,
    onSelectDestination: (HandheldRuntimeDestination) -> Unit,
) {
    if (destination == current) {
        Button(
            onClick = { onSelectDestination(destination) },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text(label)
        }
    } else {
        OutlinedButton(
            onClick = { onSelectDestination(destination) },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text(label)
        }
    }
}

private fun resolveHandheldTaskSection(section: MobileOperationsSection): MobileOperationsSection {
    return when (section) {
        MobileOperationsSection.RECEIVING,
        MobileOperationsSection.STOCK_COUNT,
        MobileOperationsSection.RESTOCK,
        MobileOperationsSection.EXPIRY,
        -> section
        MobileOperationsSection.SCAN,
        MobileOperationsSection.RUNTIME,
        -> MobileOperationsSection.RECEIVING
    }
}
