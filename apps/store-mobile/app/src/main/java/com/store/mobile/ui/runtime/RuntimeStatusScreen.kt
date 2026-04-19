package com.store.mobile.ui.runtime

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
import com.store.mobile.runtime.StoreMobileStorageSecurityPosture
import com.store.mobile.ui.scan.ScanExternalScannerStatus
import com.store.mobile.ui.scan.ZebraDataWedgeSetupStatus

data class RuntimeStatusUiState(
    val connected: Boolean,
    val title: String,
    val detail: String,
    val pendingSyncLabel: String,
    val deviceLabel: String,
    val hubLabel: String,
    val sessionLabel: String,
    val externalScannerTitle: String,
    val externalScannerDetail: String,
    val externalScannerLastScanLabel: String,
    val zebraDataWedgeTitle: String,
    val zebraDataWedgeDetail: String,
    val storageSecurityTitle: String,
    val storageSecurityDetail: String,
    val signOutLabel: String,
    val unpairLabel: String,
)

fun buildRuntimeStatusState(
    connected: Boolean,
    pendingSyncCount: Int,
    deviceId: String? = null,
    hubBaseUrl: String? = null,
    sessionExpiresAt: String? = null,
    externalScannerStatus: ScanExternalScannerStatus = ScanExternalScannerStatus.UNCONFIGURED,
    lastExternalScanAt: String? = null,
    externalScannerMessage: String? = null,
    zebraDataWedgeStatus: ZebraDataWedgeSetupStatus = ZebraDataWedgeSetupStatus.UNAVAILABLE,
    zebraDataWedgeMessage: String? = null,
    storageSecurityPosture: StoreMobileStorageSecurityPosture = StoreMobileStorageSecurityPosture.ENCRYPTED,
    storageSecurityDetail: String? = null,
): RuntimeStatusUiState {
    val normalizedPendingSyncCount = pendingSyncCount.coerceAtLeast(0)
    val deviceLabel = deviceId ?: "Awaiting paired device"
    val hubLabel = hubBaseUrl ?: "Awaiting branch hub"
    val sessionLabel = sessionExpiresAt ?: "No active runtime lease"
    val scannerTitle = when (externalScannerStatus) {
        ScanExternalScannerStatus.UNCONFIGURED -> "External scanner: Not configured"
        ScanExternalScannerStatus.READY -> "External scanner: Ready for rugged-device input"
        ScanExternalScannerStatus.RECENT_SCAN -> "External scanner: Recent scan received"
        ScanExternalScannerStatus.PAYLOAD_ERROR -> "External scanner: Scanner payload invalid"
    }
    val scannerDetail = when (externalScannerStatus) {
        ScanExternalScannerStatus.UNCONFIGURED -> "Configure the rugged-device profile to send barcode broadcasts to Store Mobile. Camera and manual fallback remain available."
        ScanExternalScannerStatus.READY -> "A valid external-scanner payload has been seen in this session and the app is ready for the next rugged-device scan."
        ScanExternalScannerStatus.RECENT_SCAN -> "A recent external scan was received successfully and flowed through the shared lookup pipeline."
        ScanExternalScannerStatus.PAYLOAD_ERROR -> "External scanner warning: ${externalScannerMessage ?: "A rugged-device broadcast was received without a usable barcode payload."}"
    }
    val lastScanLabel = "Last external scan: ${lastExternalScanAt ?: "No external scan received yet"}"
    val zebraTitle = when (zebraDataWedgeStatus) {
        ZebraDataWedgeSetupStatus.UNAVAILABLE -> "Zebra scanner setup unavailable"
        ZebraDataWedgeSetupStatus.AVAILABLE -> "Zebra DataWedge available"
        ZebraDataWedgeSetupStatus.APPLYING -> "Zebra DataWedge setup in progress"
        ZebraDataWedgeSetupStatus.CONFIGURED -> "Zebra DataWedge configured"
        ZebraDataWedgeSetupStatus.ERROR -> "Zebra DataWedge setup failed"
    }
    val zebraDetail = when (zebraDataWedgeStatus) {
        ZebraDataWedgeSetupStatus.UNAVAILABLE -> "This device does not expose Zebra DataWedge. Use camera, HID/USB, or generic external-scanner setup instead."
        ZebraDataWedgeSetupStatus.AVAILABLE -> "Zebra DataWedge is available on this device and can be configured for Store Mobile broadcast scanning."
        ZebraDataWedgeSetupStatus.APPLYING -> "Store Mobile is sending a Zebra DataWedge profile configuration request."
        ZebraDataWedgeSetupStatus.CONFIGURED -> "The Zebra-managed profile is configured for broadcast output and keystroke injection is disabled for this app."
        ZebraDataWedgeSetupStatus.ERROR -> "Zebra setup warning: ${zebraDataWedgeMessage ?: "DataWedge rejected the latest configuration request."}"
    }
    val storageTitle = when (storageSecurityPosture) {
        StoreMobileStorageSecurityPosture.ENCRYPTED -> "Storage: Encrypted preferences"
        StoreMobileStorageSecurityPosture.FALLBACK_UNENCRYPTED -> "Storage: Plain-preferences fallback"
    }
    val normalizedStorageDetail = storageSecurityDetail ?: when (storageSecurityPosture) {
        StoreMobileStorageSecurityPosture.ENCRYPTED ->
            "Pairing and runtime session data are stored in encrypted app preferences."
        StoreMobileStorageSecurityPosture.FALLBACK_UNENCRYPTED ->
            "Encrypted storage could not be initialized, so the runtime fell back to plain app preferences."
    }

    return RuntimeStatusUiState(
        connected = connected,
        title = if (connected) {
            "Connected to branch hub"
        } else {
            "Disconnected from branch hub"
        },
        detail = if (connected) {
            "This handheld is paired as a branch spoke and ready for cashier-assist and store-operations workflows."
        } else {
            "Reconnect to the approved branch hub before running live spoke operations."
        },
        pendingSyncLabel = "Pending sync actions: $normalizedPendingSyncCount",
        deviceLabel = "Device: $deviceLabel",
        hubLabel = "Hub: $hubLabel",
        sessionLabel = "Session expiry: $sessionLabel",
        externalScannerTitle = scannerTitle,
        externalScannerDetail = scannerDetail,
        externalScannerLastScanLabel = lastScanLabel,
        zebraDataWedgeTitle = zebraTitle,
        zebraDataWedgeDetail = zebraDetail,
        storageSecurityTitle = storageTitle,
        storageSecurityDetail = normalizedStorageDetail,
        signOutLabel = "Sign out",
        unpairLabel = "Unpair device",
    )
}

@Composable
fun RuntimeStatusScreen(
    state: RuntimeStatusUiState,
    onSignOut: () -> Unit = {},
    onUnpair: () -> Unit = {},
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(18.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Text(
                    text = "Runtime posture",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary,
                )
                Text(text = state.title, style = MaterialTheme.typography.headlineSmall)
                Text(text = state.detail, style = MaterialTheme.typography.bodyMedium)
                Text(
                    text = if (state.connected) {
                        "Healthy spoke connection. Session, branch, and diagnostics are ready for live handheld or tablet work."
                    } else {
                        "Recovery required. Reconnect to the approved branch hub before resuming live spoke operations."
                    },
                    style = MaterialTheme.typography.bodySmall,
                    color = if (state.connected) {
                        MaterialTheme.colorScheme.primary
                    } else {
                        MaterialTheme.colorScheme.error
                    },
                )
                Text(text = state.pendingSyncLabel, style = MaterialTheme.typography.bodyMedium)
                Text(text = state.deviceLabel, style = MaterialTheme.typography.bodyMedium)
                Text(text = state.hubLabel, style = MaterialTheme.typography.bodyMedium)
                Text(text = state.sessionLabel, style = MaterialTheme.typography.bodyMedium)
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
                    text = "Diagnostics",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary,
                )
                Text(text = state.externalScannerTitle, style = MaterialTheme.typography.titleMedium)
                Text(text = state.externalScannerDetail, style = MaterialTheme.typography.bodyMedium)
                Text(text = state.externalScannerLastScanLabel, style = MaterialTheme.typography.bodySmall)
                Text(text = state.zebraDataWedgeTitle, style = MaterialTheme.typography.titleMedium)
                Text(text = state.zebraDataWedgeDetail, style = MaterialTheme.typography.bodyMedium)
                Text(text = state.storageSecurityTitle, style = MaterialTheme.typography.titleMedium)
                Text(text = state.storageSecurityDetail, style = MaterialTheme.typography.bodyMedium)
            }
        }
        Button(
            onClick = onSignOut,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text(state.signOutLabel)
        }
        OutlinedButton(
            onClick = onUnpair,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text(state.unpairLabel)
        }
    }
}
