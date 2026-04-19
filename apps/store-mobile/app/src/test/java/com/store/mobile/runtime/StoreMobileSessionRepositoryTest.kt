package com.store.mobile.runtime

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class StoreMobileSessionRepositoryTest {
    @Test
    fun persistsRuntimeSessionAcrossLoads() {
        val repository = StoreMobilePersistentSessionRepository(InMemoryStoreMobileKeyValueStore())

        repository.saveSession(
            StoreMobileRuntimeSession(
                accessToken = "session:mobile-demo",
                expiresAt = "2099-01-01T00:00:00Z",
                deviceId = "paired-mobile-1",
                staffProfileId = "staff-demo-1",
                runtimeProfile = "mobile_store_spoke",
                sessionSurface = "store_mobile",
                tenantId = "tenant-demo-1",
                branchId = "branch-demo-1",
            ),
        )

        assertEquals("session:mobile-demo", repository.loadSession()?.accessToken)
        assertEquals("branch-demo-1", repository.loadSession()?.branchId)
    }

    @Test
    fun clearsRuntimeSession() {
        val repository = StoreMobilePersistentSessionRepository(InMemoryStoreMobileKeyValueStore())

        repository.saveSession(
            StoreMobileRuntimeSession(
                accessToken = "session:mobile-demo",
                expiresAt = "2099-01-01T00:00:00Z",
                deviceId = "paired-mobile-1",
                staffProfileId = "staff-demo-1",
                runtimeProfile = "mobile_store_spoke",
                sessionSurface = "store_mobile",
                tenantId = "tenant-demo-1",
                branchId = "branch-demo-1",
            ),
        )

        repository.clear()

        assertNull(repository.loadSession())
    }

    @Test
    fun clearingSessionPreservesPairedDeviceRecord() {
        val keyValueStore = InMemoryStoreMobileKeyValueStore()
        val pairingRepository = StoreMobilePersistentPairingRepository(keyValueStore)
        val sessionRepository = StoreMobilePersistentSessionRepository(keyValueStore)

        pairingRepository.savePairedDevice(
            deviceId = "paired-mobile-1",
            installationId = "install-1",
            runtimeProfile = "mobile_store_spoke",
            sessionSurface = "store_mobile",
            hubBaseUrl = "http://127.0.0.1:9400",
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
        )
        sessionRepository.saveSession(
            StoreMobileRuntimeSession(
                accessToken = "session:mobile-demo",
                expiresAt = "2099-01-01T00:00:00Z",
                deviceId = "paired-mobile-1",
                staffProfileId = "staff-demo-1",
                runtimeProfile = "mobile_store_spoke",
                sessionSurface = "store_mobile",
                tenantId = "tenant-demo-1",
                branchId = "branch-demo-1",
            ),
        )

        sessionRepository.clear()

        assertNull(sessionRepository.loadSession())
        assertEquals("paired-mobile-1", pairingRepository.loadPairedDevice()?.deviceId)
    }
}
