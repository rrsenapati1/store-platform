package com.store.mobile.runtime

interface StoreMobilePairingRepository {
    fun saveHubManifest(manifest: StoreMobileHubManifest)
    fun loadHubManifest(): StoreMobileHubManifest?
    fun savePairedDevice(
        deviceId: String,
        installationId: String,
        runtimeProfile: String,
        sessionSurface: String,
        hubBaseUrl: String,
    )
    fun loadPairedDevice(): StoreMobilePairedDevice?
    fun clear()
}

class InMemoryStoreMobilePairingRepository : StoreMobilePairingRepository {
    private var manifest: StoreMobileHubManifest? = null
    private var pairedDevice: StoreMobilePairedDevice? = null

    override fun saveHubManifest(manifest: StoreMobileHubManifest) {
        this.manifest = manifest
    }

    override fun loadHubManifest(): StoreMobileHubManifest? = manifest

    override fun savePairedDevice(
        deviceId: String,
        installationId: String,
        runtimeProfile: String,
        sessionSurface: String,
        hubBaseUrl: String,
    ) {
        pairedDevice = StoreMobilePairedDevice(
            deviceId = deviceId,
            installationId = installationId,
            runtimeProfile = runtimeProfile,
            sessionSurface = sessionSurface,
            hubBaseUrl = hubBaseUrl,
        )
    }

    override fun loadPairedDevice(): StoreMobilePairedDevice? = pairedDevice

    override fun clear() {
        manifest = null
        pairedDevice = null
    }
}
