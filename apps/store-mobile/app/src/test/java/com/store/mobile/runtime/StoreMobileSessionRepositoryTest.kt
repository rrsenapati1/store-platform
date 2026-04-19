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
}
