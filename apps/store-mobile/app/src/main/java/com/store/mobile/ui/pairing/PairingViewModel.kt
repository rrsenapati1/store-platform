package com.store.mobile.ui.pairing

import com.store.mobile.runtime.StoreMobileHubClient
import com.store.mobile.runtime.StoreMobilePairedDevice
import com.store.mobile.runtime.StoreMobilePairingRepository
import com.store.mobile.runtime.StoreMobileRuntimeSession
import com.store.mobile.runtime.StoreMobileSessionRepository
import com.store.mobile.runtime.parseStoreMobileExpiryMillis

enum class PairingSessionStatus {
    UNPAIRED,
    ACTIVE,
    SIGNED_OUT,
    EXPIRED,
}

data class PairingUiState(
    val hubBaseUrl: String = "",
    val activationCode: String = "",
    val requestedSessionSurface: String = "store_mobile",
    val canRedeemActivation: Boolean = false,
    val pairedDevice: StoreMobilePairedDevice? = null,
    val sessionStatus: PairingSessionStatus = PairingSessionStatus.UNPAIRED,
    val errorMessage: String? = null,
)

class PairingViewModel(
    private val pairingRepository: StoreMobilePairingRepository,
    private val sessionRepository: StoreMobileSessionRepository,
    private val hubClient: StoreMobileHubClient,
) {
    var state: PairingUiState = buildState()
        private set

    fun updateManualActivation(hubBaseUrl: String, activationCode: String) {
        state = state.copy(
            hubBaseUrl = hubBaseUrl,
            activationCode = activationCode,
            canRedeemActivation = hubBaseUrl.isNotBlank() && activationCode.isNotBlank(),
            errorMessage = null,
        )
    }

    fun updateRequestedSessionSurface(requestedSessionSurface: String) {
        state = state.copy(
            requestedSessionSurface = requestedSessionSurface,
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
            requestedSessionSurface = state.requestedSessionSurface,
        )
        pairingRepository.savePairedDevice(
            deviceId = session.deviceId,
            installationId = installationId,
            runtimeProfile = session.runtimeProfile,
            sessionSurface = session.sessionSurface,
            hubBaseUrl = state.hubBaseUrl,
            tenantId = session.tenantId,
            branchId = session.branchId,
        )
        sessionRepository.saveSession(session)
        state = buildState(
            activationCode = "",
            errorMessage = null,
            requestedSessionSurface = state.requestedSessionSurface,
        )
    }

    fun signOutSession() {
        sessionRepository.clear()
        state = buildState(
            activationCode = "",
            errorMessage = null,
            requestedSessionSurface = state.requestedSessionSurface,
        )
    }

    fun unpairDevice() {
        sessionRepository.clear()
        pairingRepository.clear()
        state = buildState(
            activationCode = "",
            errorMessage = null,
            requestedSessionSurface = "store_mobile",
        )
    }

    fun handleExpiredSession() {
        sessionRepository.clear()
        state = buildState(
            activationCode = "",
            errorMessage = "Runtime session expired. Redeem a fresh activation or unpair this device.",
            requestedSessionSurface = state.requestedSessionSurface,
        )
    }

    private fun buildState(
        activationCode: String = "",
        errorMessage: String? = null,
        requestedSessionSurface: String = "store_mobile",
    ): PairingUiState {
        val pairedDevice = pairingRepository.loadPairedDevice()
        val persistedSession = sessionRepository.loadSession()
        val expiredSession = persistedSession?.takeIf { isSessionExpired(it) }
        if (expiredSession != null) {
            sessionRepository.clear()
        }
        val sessionStatus = when {
            pairedDevice == null -> PairingSessionStatus.UNPAIRED
            persistedSession == null -> PairingSessionStatus.SIGNED_OUT
            expiredSession != null -> PairingSessionStatus.EXPIRED
            else -> PairingSessionStatus.ACTIVE
        }
        return PairingUiState(
            hubBaseUrl = pairedDevice?.hubBaseUrl ?: "",
            activationCode = activationCode,
            requestedSessionSurface = pairedDevice?.sessionSurface ?: requestedSessionSurface,
            canRedeemActivation = (pairedDevice?.hubBaseUrl ?: "").isNotBlank() && activationCode.isNotBlank(),
            pairedDevice = pairedDevice,
            sessionStatus = sessionStatus,
            errorMessage = errorMessage ?: if (sessionStatus == PairingSessionStatus.EXPIRED) {
                "Runtime session expired. Redeem a fresh activation or unpair this device."
            } else {
                null
            },
        )
    }

    private fun isSessionExpired(session: StoreMobileRuntimeSession): Boolean {
        val expiresAtMillis = parseStoreMobileExpiryMillis(session.expiresAt)
            ?: return true
        return expiresAtMillis <= System.currentTimeMillis()
    }
}
