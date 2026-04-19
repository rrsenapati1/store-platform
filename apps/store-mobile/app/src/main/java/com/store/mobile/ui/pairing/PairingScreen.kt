package com.store.mobile.ui.pairing

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.store.mobile.ui.pairing.PairingSessionStatus.ACTIVE
import com.store.mobile.ui.pairing.PairingSessionStatus.EXPIRED
import com.store.mobile.ui.pairing.PairingSessionStatus.SIGNED_OUT

@Composable
fun PairingScreen(
    state: PairingUiState,
    onHubBaseUrlChange: (String) -> Unit,
    onActivationCodeChange: (String) -> Unit,
    onRequestedSessionSurfaceChange: (String) -> Unit,
    onRedeemActivation: () -> Unit,
    onUnpairDevice: () -> Unit,
) {
    val title = when (state.sessionStatus) {
        EXPIRED -> "Runtime session expired"
        SIGNED_OUT -> "Resume paired runtime"
        else -> "Pair Android runtime"
    }
    val subtitle = when (state.sessionStatus) {
        EXPIRED -> "This device is still paired, but the live runtime session expired. Redeem a fresh activation or unpair it."
        SIGNED_OUT -> "This device remains paired to its hub, but no live operator session is active. Redeem a fresh activation to continue."
        ACTIVE -> "This paired device already has a live session."
        else -> "Manual activation is ready. QR pairing will reuse the same runtime contract later."
    }
    val redeemLabel = if (state.pairedDevice != null) "Redeem fresh activation" else "Redeem activation"

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(
            text = title,
            style = MaterialTheme.typography.headlineSmall,
        )
        Text(
            text = subtitle,
            style = MaterialTheme.typography.bodyMedium,
        )
        state.pairedDevice?.let { device ->
            Text(
                text = "Paired as ${device.runtimeProfile} on ${device.hubBaseUrl}",
                style = MaterialTheme.typography.bodyMedium,
            )
            Button(
                onClick = onUnpairDevice,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("Unpair device")
            }
        }
        Text(
            text = "Device mode",
            style = MaterialTheme.typography.titleMedium,
        )
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Button(
                onClick = { onRequestedSessionSurfaceChange("store_mobile") },
                enabled = state.requestedSessionSurface != "store_mobile",
                modifier = Modifier.weight(1f),
            ) {
                Text("Handheld")
            }
            Button(
                onClick = { onRequestedSessionSurfaceChange("inventory_tablet") },
                enabled = state.requestedSessionSurface != "inventory_tablet",
                modifier = Modifier.weight(1f),
            ) {
                Text("Inventory tablet")
            }
        }
        OutlinedTextField(
            value = state.hubBaseUrl,
            onValueChange = onHubBaseUrlChange,
            label = { Text("Hub URL") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )
        OutlinedTextField(
            value = state.activationCode,
            onValueChange = onActivationCodeChange,
            label = { Text("Activation code") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )
        Button(
            onClick = onRedeemActivation,
            enabled = state.canRedeemActivation,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text(redeemLabel)
        }
    }
}
