package com.store.mobile.ui.entry

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.store.mobile.ui.pairing.PairingScreen
import com.store.mobile.ui.pairing.PairingSessionStatus
import com.store.mobile.ui.pairing.PairingUiState

@Composable
fun StoreMobileEntrySurface(
    state: PairingUiState,
    onHubBaseUrlChange: (String) -> Unit,
    onActivationCodeChange: (String) -> Unit,
    onRequestedSessionSurfaceChange: (String) -> Unit,
    onRedeemActivation: () -> Unit,
    onUnpairDevice: () -> Unit,
) {
    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background,
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(18.dp),
        ) {
            EntryStatusCard(state = state)
            PairingScreen(
                state = state,
                onHubBaseUrlChange = onHubBaseUrlChange,
                onActivationCodeChange = onActivationCodeChange,
                onRequestedSessionSurfaceChange = onRequestedSessionSurfaceChange,
                onRedeemActivation = onRedeemActivation,
                onUnpairDevice = onUnpairDevice,
            )
        }
    }
}

@Composable
private fun EntryStatusCard(state: PairingUiState) {
    val title = when (state.sessionStatus) {
        PairingSessionStatus.EXPIRED -> "Session recovery required"
        PairingSessionStatus.SIGNED_OUT -> "Paired runtime ready"
        PairingSessionStatus.ACTIVE -> "Runtime session active"
        PairingSessionStatus.UNPAIRED -> "Activate this device"
    }
    val detail = when (state.sessionStatus) {
        PairingSessionStatus.EXPIRED -> "This handheld is still approved for the branch, but the live operator session expired. Recover it here before returning to tasks."
        PairingSessionStatus.SIGNED_OUT -> "This device remains paired to the branch hub. Redeem a fresh activation to resume associate work."
        PairingSessionStatus.ACTIVE -> "A live runtime session is already active on this device."
        PairingSessionStatus.UNPAIRED -> "Pair this device to the branch hub, then redeem an activation for handheld or tablet work."
    }

    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(
                text = "Store Mobile",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary,
            )
            Text(
                text = title,
                style = MaterialTheme.typography.headlineSmall,
            )
            Text(
                text = detail,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            state.pairedDevice?.let { device ->
                Text(
                    text = "Paired device ${device.deviceId} · ${device.runtimeProfile} · ${device.branchId}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}
