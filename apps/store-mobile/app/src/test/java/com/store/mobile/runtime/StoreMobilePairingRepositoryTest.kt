package com.store.mobile.runtime

import org.junit.Assert.assertEquals
import org.junit.Test

class StoreMobilePairingRepositoryTest {
    @Test
    fun persistsHubManifestAndPairedDeviceContext() {
        val repository = InMemoryStoreMobilePairingRepository()

        repository.savePairedDevice(
            deviceId = "device-1",
            installationId = "install-1",
            runtimeProfile = "mobile_store_spoke",
            sessionSurface = "store_mobile",
            hubBaseUrl = "http://127.0.0.1:9400",
        )

        assertEquals("device-1", repository.loadPairedDevice()?.deviceId)
    }
}
