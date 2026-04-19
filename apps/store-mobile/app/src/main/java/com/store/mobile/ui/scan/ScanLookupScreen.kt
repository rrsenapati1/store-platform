package com.store.mobile.ui.scan

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.input.key.Key
import androidx.compose.ui.input.key.KeyEventType
import androidx.compose.ui.input.key.key
import androidx.compose.ui.input.key.onPreviewKeyEvent
import androidx.compose.ui.input.key.type
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import com.store.mobile.ui.handheld.HandheldScanHomeScreen
import com.store.mobile.ui.handheld.buildHandheldScanActionModel
import com.store.mobile.ui.operations.ExpiryUiState
import com.store.mobile.ui.operations.MobileOperationsSection
import com.store.mobile.ui.operations.ReceivingUiState
import com.store.mobile.ui.operations.RestockUiState
import com.store.mobile.ui.operations.StockCountUiState

@Composable
fun ScanLookupScreen(
    state: ScanLookupUiState,
    isTabletLayout: Boolean,
    onDraftBarcodeChange: (String) -> Unit,
    onLookupBarcode: () -> Unit,
    onConfigureZebraDataWedge: () -> Unit,
    onCameraPermissionResolved: (Boolean) -> Unit,
    onCameraPreviewFailure: (String) -> Unit,
    onCameraBarcodeDetected: (String) -> Unit,
    receivingState: ReceivingUiState = ReceivingUiState(),
    stockCountState: StockCountUiState = StockCountUiState(),
    restockState: RestockUiState = RestockUiState(),
    expiryState: ExpiryUiState = ExpiryUiState(),
    onSelectTaskSection: (MobileOperationsSection) -> Unit = {},
) {
    val context = LocalContext.current
    val permissionGranted = ContextCompat.checkSelfPermission(
        context,
        Manifest.permission.CAMERA,
    ) == PackageManager.PERMISSION_GRANTED
    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission(),
        onResult = onCameraPermissionResolved,
    )
    val barcodeFieldFocusRequester = remember { FocusRequester() }

    LaunchedEffect(permissionGranted) {
        onCameraPermissionResolved(permissionGranted)
    }

    LaunchedEffect(Unit) {
        barcodeFieldFocusRequester.requestFocus()
    }

    if (isTabletLayout) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            horizontalArrangement = Arrangement.spacedBy(20.dp),
        ) {
            ScanCameraPanel(
                modifier = Modifier.weight(0.56f),
                state = state,
                onRequestPermission = { permissionLauncher.launch(Manifest.permission.CAMERA) },
                onRetryCamera = { onCameraPermissionResolved(permissionGranted) },
                onCameraPreviewFailure = onCameraPreviewFailure,
                onCameraBarcodeDetected = onCameraBarcodeDetected,
            )
            ScanLookupDetailsPanel(
                modifier = Modifier.weight(0.44f),
                state = state,
                focusRequester = barcodeFieldFocusRequester,
                onDraftBarcodeChange = onDraftBarcodeChange,
                onLookupBarcode = onLookupBarcode,
                onConfigureZebraDataWedge = onConfigureZebraDataWedge,
            )
        }
    } else {
        val actionModel = buildHandheldScanActionModel(
            scanState = state,
            receivingState = receivingState,
            stockCountState = stockCountState,
            restockState = restockState,
            expiryState = expiryState,
        )
        HandheldScanHomeScreen(
            state = state,
            focusRequester = barcodeFieldFocusRequester,
            actionModel = actionModel,
            onDraftBarcodeChange = onDraftBarcodeChange,
            onLookupBarcode = onLookupBarcode,
            onConfigureZebraDataWedge = onConfigureZebraDataWedge,
            onSelectTaskSection = onSelectTaskSection,
        )
    }
}

@Composable
internal fun ScanCameraPanel(
    modifier: Modifier,
    state: ScanLookupUiState,
    onRequestPermission: () -> Unit,
    onRetryCamera: () -> Unit,
    onCameraPreviewFailure: (String) -> Unit,
    onCameraBarcodeDetected: (String) -> Unit,
) {
    Column(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(
            text = "Scan and lookup",
            style = MaterialTheme.typography.headlineSmall,
        )
        Text(
            text = "Use live camera preview for instant catalog lookup, or fall back to manual barcode entry when needed.",
            style = MaterialTheme.typography.bodyMedium,
        )

        when (state.cameraStatus) {
            ScanCameraStatus.CHECKING -> {
                ScanCameraMessageCard(
                    title = "Checking camera access",
                    message = "Preparing the live barcode scanner for this device.",
                )
            }

            ScanCameraStatus.PERMISSION_REQUIRED -> {
                ScanCameraMessageCard(
                    title = "Camera permission required",
                    message = "Allow camera access to scan barcodes live on this device.",
                    actionLabel = "Allow camera",
                    onAction = onRequestPermission,
                )
            }

            ScanCameraStatus.READY -> {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(280.dp)
                        .clip(RoundedCornerShape(20.dp))
                        .background(MaterialTheme.colorScheme.surfaceVariant),
                ) {
                    CameraBarcodePreview(
                        modifier = Modifier.fillMaxSize(),
                        onBarcodeDetected = onCameraBarcodeDetected,
                        onCameraFailure = onCameraPreviewFailure,
                    )
                }
            }

            ScanCameraStatus.UNAVAILABLE -> {
                ScanCameraMessageCard(
                    title = "Camera unavailable",
                    message = state.cameraMessage
                        ?: "Live preview could not start. Manual barcode entry is still available.",
                    actionLabel = "Retry camera",
                    onAction = onRetryCamera,
                )
            }
        }
    }
}

@Composable
internal fun ScanLookupDetailsPanel(
    modifier: Modifier,
    state: ScanLookupUiState,
    focusRequester: FocusRequester,
    onDraftBarcodeChange: (String) -> Unit,
    onLookupBarcode: () -> Unit,
    onConfigureZebraDataWedge: () -> Unit,
) {
    Column(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        OutlinedTextField(
            value = state.draftBarcode,
            onValueChange = onDraftBarcodeChange,
            label = { Text("Barcode") },
            modifier = Modifier
                .fillMaxWidth()
                .focusRequester(focusRequester)
                .onPreviewKeyEvent { event ->
                    if (event.type == KeyEventType.KeyUp && event.key == Key.Enter) {
                        onLookupBarcode()
                        true
                    } else {
                        false
                    }
                },
            singleLine = true,
            keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
            keyboardActions = KeyboardActions(
                onSearch = {
                    onLookupBarcode()
                },
            ),
        )
        Button(
            onClick = onLookupBarcode,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Lookup barcode")
        }
        ExternalScannerStatusCard(state = state)
        ZebraDataWedgeStatusCard(
            state = state,
            onConfigureZebraDataWedge = onConfigureZebraDataWedge,
        )
        if (state.productName.isNotBlank()) {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    Text(text = state.productName, style = MaterialTheme.typography.titleLarge)
                    Text(
                        text = scanSourceLabel(state.lastScanSource),
                        style = MaterialTheme.typography.labelLarge,
                        color = MaterialTheme.colorScheme.primary,
                    )
                    Text(text = "Barcode: ${state.barcode}", style = MaterialTheme.typography.bodyMedium)
                    Text(text = "SKU: ${state.skuCode}", style = MaterialTheme.typography.bodyMedium)
                    Text(text = "Price: ${state.priceLabel}", style = MaterialTheme.typography.bodyMedium)
                    Text(text = "Stock: ${state.stockLabel}", style = MaterialTheme.typography.bodyMedium)
                    Text(text = "Status: ${state.availabilityStatus}", style = MaterialTheme.typography.bodyMedium)
                }
            }
        }
        state.errorMessage?.let { message ->
            Text(
                text = message,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.error,
            )
        }
        if (state.cameraStatus == ScanCameraStatus.READY) {
            Text(
                text = "Point the camera at a barcode, or use a DataWedge/HID/USB external scanner. Repeated detections are throttled to keep lookup stable.",
                style = MaterialTheme.typography.bodyMedium,
            )
        }
    }
}

@Composable
private fun ExternalScannerStatusCard(state: ScanLookupUiState) {
    val title = when (state.externalScannerStatus) {
        ScanExternalScannerStatus.UNCONFIGURED -> "External scanner not configured"
        ScanExternalScannerStatus.READY -> "Ready for external scanner input"
        ScanExternalScannerStatus.RECENT_SCAN -> "Last external scan received"
        ScanExternalScannerStatus.PAYLOAD_ERROR -> "Scanner payload invalid"
    }
    val detail = when (state.externalScannerStatus) {
        ScanExternalScannerStatus.UNCONFIGURED -> "Waiting for the first rugged-device scanner payload in this session. Camera and manual fallback are still available."
        ScanExternalScannerStatus.READY -> "A rugged-device scanner has already been validated in this session and the app is listening for the next scan."
        ScanExternalScannerStatus.RECENT_SCAN -> "External scanner traffic is flowing into the shared lookup path."
        ScanExternalScannerStatus.PAYLOAD_ERROR -> state.externalScannerMessage
            ?: "The latest rugged-device scanner broadcast did not include a usable barcode."
    }
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text(text = title, style = MaterialTheme.typography.titleMedium)
            Text(text = detail, style = MaterialTheme.typography.bodyMedium)
            Text(
                text = "Last external scan: ${state.lastExternalScanAt ?: "No external scan received yet"}",
                style = MaterialTheme.typography.bodySmall,
            )
        }
    }
}

@Composable
private fun ZebraDataWedgeStatusCard(
    state: ScanLookupUiState,
    onConfigureZebraDataWedge: () -> Unit,
) {
    if (state.zebraDataWedgeStatus == ZebraDataWedgeSetupStatus.UNAVAILABLE) {
        return
    }

    val title = when (state.zebraDataWedgeStatus) {
        ZebraDataWedgeSetupStatus.UNAVAILABLE -> ""
        ZebraDataWedgeSetupStatus.AVAILABLE -> "Zebra DataWedge available"
        ZebraDataWedgeSetupStatus.APPLYING -> "Configuring Zebra DataWedge"
        ZebraDataWedgeSetupStatus.CONFIGURED -> "Zebra DataWedge configured"
        ZebraDataWedgeSetupStatus.ERROR -> "Zebra DataWedge setup failed"
    }
    val detail = when (state.zebraDataWedgeStatus) {
        ZebraDataWedgeSetupStatus.UNAVAILABLE -> ""
        ZebraDataWedgeSetupStatus.AVAILABLE -> "This Zebra device can configure a Store Mobile broadcast profile with one tap."
        ZebraDataWedgeSetupStatus.APPLYING -> "Waiting for the Zebra DataWedge result action from the latest setup request."
        ZebraDataWedgeSetupStatus.CONFIGURED -> "The Zebra-managed profile is configured for broadcast output and keystroke injection is disabled for this app."
        ZebraDataWedgeSetupStatus.ERROR -> state.zebraDataWedgeMessage
            ?: "DataWedge rejected the latest Store Mobile setup request."
    }
    val actionLabel = when (state.zebraDataWedgeStatus) {
        ZebraDataWedgeSetupStatus.AVAILABLE -> "Configure Zebra DataWedge"
        ZebraDataWedgeSetupStatus.ERROR -> "Retry Zebra setup"
        ZebraDataWedgeSetupStatus.CONFIGURED -> "Reconfigure Zebra DataWedge"
        ZebraDataWedgeSetupStatus.APPLYING,
        ZebraDataWedgeSetupStatus.UNAVAILABLE,
        -> null
    }

    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(text = title, style = MaterialTheme.typography.titleMedium)
            Text(text = detail, style = MaterialTheme.typography.bodyMedium)
            if (actionLabel != null) {
                OutlinedButton(onClick = onConfigureZebraDataWedge) {
                    Text(actionLabel)
                }
            }
        }
    }
}

private fun scanSourceLabel(source: ScanLookupSource): String {
    return when (source) {
        ScanLookupSource.MANUAL -> "Manual lookup"
        ScanLookupSource.CAMERA -> "Live camera scan"
        ScanLookupSource.EXTERNAL_SCANNER -> "External scanner"
    }
}

@Composable
private fun ScanCameraMessageCard(
    title: String,
    message: String,
    actionLabel: String? = null,
    onAction: (() -> Unit)? = null,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text(text = title, style = MaterialTheme.typography.titleMedium)
            Text(text = message, style = MaterialTheme.typography.bodyMedium)
            if (actionLabel != null && onAction != null) {
                Button(onClick = onAction) {
                    Text(actionLabel)
                }
            }
        }
    }
}
