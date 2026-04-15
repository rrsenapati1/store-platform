package com.store.mobile.ui.runtime

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.store.mobile.ui.scan.ScanExternalScannerStatus

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
    )
}

@Composable
fun RuntimeStatusScreen(state: RuntimeStatusUiState) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(text = state.title, style = MaterialTheme.typography.headlineSmall)
        Text(text = state.detail, style = MaterialTheme.typography.bodyMedium)
        Text(text = state.pendingSyncLabel, style = MaterialTheme.typography.bodyMedium)
        Text(text = state.deviceLabel, style = MaterialTheme.typography.bodyMedium)
        Text(text = state.hubLabel, style = MaterialTheme.typography.bodyMedium)
        Text(text = state.sessionLabel, style = MaterialTheme.typography.bodyMedium)
        Text(text = state.externalScannerTitle, style = MaterialTheme.typography.bodyMedium)
        Text(text = state.externalScannerDetail, style = MaterialTheme.typography.bodyMedium)
        Text(text = state.externalScannerLastScanLabel, style = MaterialTheme.typography.bodyMedium)
    }
}
