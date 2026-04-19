package com.store.mobile.runtime

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class StoreMobilePairingRepositoryTest {
    @Test
    fun persistsHubManifestAndPairedDeviceContext() {
        val repository = StoreMobilePersistentPairingRepository(InMemoryStoreMobileKeyValueStore())

        repository.saveHubManifest(
            StoreMobileHubManifest(
                hubBaseUrl = "http://127.0.0.1:9400",
                hubDeviceId = "hub-demo-1",
                runtimeProfiles = listOf("mobile_store_spoke", "inventory_tablet_spoke"),
                pairingModes = listOf("qr", "approval_code"),
            ),
        )

        repository.savePairedDevice(
            deviceId = "device-1",
            installationId = "install-1",
            runtimeProfile = "mobile_store_spoke",
            sessionSurface = "store_mobile",
            hubBaseUrl = "http://127.0.0.1:9400",
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
        )

        assertEquals("device-1", repository.loadPairedDevice()?.deviceId)
        assertEquals("tenant-demo-1", repository.loadPairedDevice()?.tenantId)
        assertEquals("branch-demo-1", repository.loadPairedDevice()?.branchId)
        assertEquals("hub-demo-1", repository.loadHubManifest()?.hubDeviceId)
    }

    @Test
    fun clearsManifestAndPairedDeviceContext() {
        val repository = StoreMobilePersistentPairingRepository(InMemoryStoreMobileKeyValueStore())

        repository.savePairedDevice(
            deviceId = "device-1",
            installationId = "install-1",
            runtimeProfile = "mobile_store_spoke",
            sessionSurface = "store_mobile",
            hubBaseUrl = "http://127.0.0.1:9400",
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
        )

        repository.clear()

        assertNull(repository.loadPairedDevice())
        assertNull(repository.loadHubManifest())
    }
}
