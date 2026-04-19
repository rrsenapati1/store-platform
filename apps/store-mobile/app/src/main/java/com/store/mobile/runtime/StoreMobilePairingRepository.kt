package com.store.mobile.runtime

import org.json.JSONObject

interface StoreMobilePairingRepository {
    fun saveHubManifest(manifest: StoreMobileHubManifest)
    fun loadHubManifest(): StoreMobileHubManifest?
    fun savePairedDevice(
        deviceId: String,
        installationId: String,
        runtimeProfile: String,
        sessionSurface: String,
        hubBaseUrl: String,
        tenantId: String,
        branchId: String,
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
        tenantId: String,
        branchId: String,
    ) {
        pairedDevice = StoreMobilePairedDevice(
            deviceId = deviceId,
            installationId = installationId,
            runtimeProfile = runtimeProfile,
            sessionSurface = sessionSurface,
            hubBaseUrl = hubBaseUrl,
            tenantId = tenantId,
            branchId = branchId,
        )
    }

    override fun loadPairedDevice(): StoreMobilePairedDevice? = pairedDevice

    override fun clear() {
        manifest = null
        pairedDevice = null
    }
}

class StoreMobilePersistentPairingRepository(
    private val keyValueStore: StoreMobileKeyValueStore,
) : StoreMobilePairingRepository {
    override fun saveHubManifest(manifest: StoreMobileHubManifest) {
        keyValueStore.putString(HUB_MANIFEST_KEY, manifest.toJson().toString())
    }

    override fun loadHubManifest(): StoreMobileHubManifest? {
        val raw = keyValueStore.getString(HUB_MANIFEST_KEY) ?: return null
        return runCatching { JSONObject(raw).toHubManifest() }.getOrNull()
    }

    override fun savePairedDevice(
        deviceId: String,
        installationId: String,
        runtimeProfile: String,
        sessionSurface: String,
        hubBaseUrl: String,
        tenantId: String,
        branchId: String,
    ) {
        val pairedDevice = StoreMobilePairedDevice(
            deviceId = deviceId,
            installationId = installationId,
            runtimeProfile = runtimeProfile,
            sessionSurface = sessionSurface,
            hubBaseUrl = hubBaseUrl,
            tenantId = tenantId,
            branchId = branchId,
        )
        keyValueStore.putString(PAIRED_DEVICE_KEY, pairedDevice.toJson().toString())
    }

    override fun loadPairedDevice(): StoreMobilePairedDevice? {
        val raw = keyValueStore.getString(PAIRED_DEVICE_KEY) ?: return null
        return runCatching { JSONObject(raw).toPairedDevice() }.getOrNull()
    }

    override fun clear() {
        keyValueStore.remove(HUB_MANIFEST_KEY)
        keyValueStore.remove(PAIRED_DEVICE_KEY)
    }

    private fun StoreMobileHubManifest.toJson(): JSONObject {
        return JSONObject()
            .put("hubBaseUrl", hubBaseUrl)
            .put("hubDeviceId", hubDeviceId)
            .put("runtimeProfiles", runtimeProfiles)
            .put("pairingModes", pairingModes)
    }

    private fun JSONObject.toHubManifest(): StoreMobileHubManifest {
        return StoreMobileHubManifest(
            hubBaseUrl = getString("hubBaseUrl"),
            hubDeviceId = getString("hubDeviceId"),
            runtimeProfiles = getJSONArray("runtimeProfiles").toStringList(),
            pairingModes = getJSONArray("pairingModes").toStringList(),
        )
    }

    private fun StoreMobilePairedDevice.toJson(): JSONObject {
        return JSONObject()
            .put("deviceId", deviceId)
            .put("installationId", installationId)
            .put("runtimeProfile", runtimeProfile)
            .put("sessionSurface", sessionSurface)
            .put("hubBaseUrl", hubBaseUrl)
            .put("tenantId", tenantId)
            .put("branchId", branchId)
    }

    private fun JSONObject.toPairedDevice(): StoreMobilePairedDevice {
        return StoreMobilePairedDevice(
            deviceId = getString("deviceId"),
            installationId = getString("installationId"),
            runtimeProfile = getString("runtimeProfile"),
            sessionSurface = getString("sessionSurface"),
            hubBaseUrl = getString("hubBaseUrl"),
            tenantId = getString("tenantId"),
            branchId = getString("branchId"),
        )
    }

    private fun org.json.JSONArray.toStringList(): List<String> {
        return buildList(length()) {
            for (index in 0 until length()) {
                add(getString(index))
            }
        }
    }

    private companion object {
        const val HUB_MANIFEST_KEY = "store.mobile.hub_manifest"
        const val PAIRED_DEVICE_KEY = "store.mobile.paired_device"
    }
}
