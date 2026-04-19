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
    val model = buildStoreMobileEntryStatusModel(state)

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
                text = model.eyebrow,
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text(
                text = model.title,
                style = MaterialTheme.typography.headlineSmall,
            )
            Text(
                text = model.detail,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text(
                text = model.actionHint,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.primary,
            )
            state.pairedDevice?.let { device ->
                Text(
                    text = "Paired device ${device.deviceId} · ${device.runtimeProfile} · ${device.branchId}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            state.errorMessage?.let { message ->
                Text(
                    text = message,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.error,
                )
            }
        }
    }
}
