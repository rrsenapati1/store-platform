package com.store.mobile.ui.pairing

import com.store.mobile.runtime.StoreMobileHubClient
import com.store.mobile.runtime.StoreMobilePairedDevice
import com.store.mobile.runtime.StoreMobilePairingRepository
import com.store.mobile.runtime.StoreMobileSessionRepository

data class PairingUiState(
    val hubBaseUrl: String = "",
    val activationCode: String = "",
    val canRedeemActivation: Boolean = false,
    val pairedDevice: StoreMobilePairedDevice? = null,
    val errorMessage: String? = null,
)

class PairingViewModel(
    private val pairingRepository: StoreMobilePairingRepository,
    private val sessionRepository: StoreMobileSessionRepository,
    private val hubClient: StoreMobileHubClient,
) {
    var state: PairingUiState = PairingUiState(
        pairedDevice = pairingRepository.loadPairedDevice(),
    )
        private set

    fun updateManualActivation(hubBaseUrl: String, activationCode: String) {
        state = state.copy(
            hubBaseUrl = hubBaseUrl,
            activationCode = activationCode,
            canRedeemActivation = hubBaseUrl.isNotBlank() && activationCode.isNotBlank(),
            errorMessage = null,
        )
    }

    fun redeemManualActivation(installationId: String) {
        if (!state.canRedeemActivation) {
            state = state.copy(errorMessage = "Hub URL and activation code are required.")
            return
        }

        val manifest = hubClient.fetchManifest(state.hubBaseUrl)
        pairingRepository.saveHubManifest(manifest)
        val session = hubClient.redeemActivation(
            hubBaseUrl = state.hubBaseUrl,
            installationId = installationId,
            activationCode = state.activationCode,
        )
        pairingRepository.savePairedDevice(
            deviceId = session.deviceId,
            installationId = installationId,
            runtimeProfile = session.runtimeProfile,
            sessionSurface = session.sessionSurface,
            hubBaseUrl = state.hubBaseUrl,
        )
        sessionRepository.saveSession(session)
        state = state.copy(
            pairedDevice = pairingRepository.loadPairedDevice(),
            errorMessage = null,
        )
    }
}
