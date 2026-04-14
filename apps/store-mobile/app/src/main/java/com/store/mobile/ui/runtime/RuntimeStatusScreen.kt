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

data class RuntimeStatusUiState(
    val connected: Boolean,
    val title: String,
    val detail: String,
    val pendingSyncLabel: String,
    val deviceLabel: String,
    val hubLabel: String,
    val sessionLabel: String,
)

fun buildRuntimeStatusState(
    connected: Boolean,
    pendingSyncCount: Int,
    deviceId: String? = null,
    hubBaseUrl: String? = null,
    sessionExpiresAt: String? = null,
): RuntimeStatusUiState {
    val normalizedPendingSyncCount = pendingSyncCount.coerceAtLeast(0)
    val deviceLabel = deviceId ?: "Awaiting paired device"
    val hubLabel = hubBaseUrl ?: "Awaiting branch hub"
    val sessionLabel = sessionExpiresAt ?: "No active runtime lease"

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
    }
}
