package com.store.mobile.ui

import com.store.mobile.operations.InMemoryStockCountRepository
import com.store.mobile.operations.InMemoryExpiryRepository
import com.store.mobile.operations.InMemoryReceivingRepository
import com.store.mobile.operations.InMemoryRestockRepository
import com.store.mobile.operations.RemoteExpiryRepository
import com.store.mobile.operations.RemoteReceivingRepository
import com.store.mobile.operations.RemoteRestockRepository
import com.store.mobile.operations.RemoteStockCountRepository
import com.store.mobile.runtime.StoreMobilePairedDevice
import com.store.mobile.runtime.StoreMobileRuntimeSession
import com.store.mobile.scan.InMemoryScanLookupRepository
import com.store.mobile.scan.RemoteScanLookupRepository
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class StoreMobileRuntimeContextTest {
    @Test
    fun resolvesOperationalBranchIdFromRuntimeContext() {
        val pairedDevice = StoreMobilePairedDevice(
            deviceId = "device-1",
            installationId = "installation-1",
            runtimeProfile = "inventory_tablet_spoke",
            sessionSurface = "inventory_tablet",
            hubBaseUrl = "http://10.0.2.2:8000",
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
        )
        val session = StoreMobileRuntimeSession(
            accessToken = "session-token",
            expiresAt = "2026-04-16T10:00:00Z",
            deviceId = "device-1",
            staffProfileId = "staff-1",
            runtimeProfile = "inventory_tablet_spoke",
            sessionSurface = "inventory_tablet",
            tenantId = "tenant-demo-1",
            branchId = "branch-live-42",
        )

        val branchId = resolveStoreMobileOperationsBranchId(
            pairedDevice = pairedDevice,
            session = session,
        )

        assertEquals("branch-live-42", branchId)
    }

    @Test
    fun buildsRemoteStockCountRepositoryWhenPairedRuntimeContextExists() {
        val pairedDevice = StoreMobilePairedDevice(
            deviceId = "device-1",
            installationId = "installation-1",
            runtimeProfile = "mobile_store_spoke",
            sessionSurface = "store_mobile",
            hubBaseUrl = "http://10.0.2.2:8000",
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
        )
        val session = StoreMobileRuntimeSession(
            accessToken = "session-token",
            expiresAt = "2026-04-16T10:00:00Z",
            deviceId = "device-1",
            staffProfileId = "staff-1",
            runtimeProfile = "mobile_store_spoke",
            sessionSurface = "store_mobile",
            tenantId = "tenant-live-1",
            branchId = "branch-live-42",
        )

        val repository = buildStoreMobileStockCountRepository(
            pairedDevice = pairedDevice,
            session = session,
        )

        assertTrue(repository is RemoteStockCountRepository)
    }

    @Test
    fun fallsBackToInMemoryStockCountRepositoryWithoutRuntimeSession() {
        val repository = buildStoreMobileStockCountRepository(
            pairedDevice = null,
            session = null,
        )

        assertTrue(repository is InMemoryStockCountRepository)
    }

    @Test
    fun buildsRemoteReceivingRepositoryWhenPairedRuntimeContextExists() {
        val pairedDevice = StoreMobilePairedDevice(
            deviceId = "device-1",
            installationId = "installation-1",
            runtimeProfile = "mobile_store_spoke",
            sessionSurface = "store_mobile",
            hubBaseUrl = "http://10.0.2.2:8000",
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
        )
        val session = StoreMobileRuntimeSession(
            accessToken = "session-token",
            expiresAt = "2026-04-16T10:00:00Z",
            deviceId = "device-1",
            staffProfileId = "staff-1",
            runtimeProfile = "mobile_store_spoke",
            sessionSurface = "store_mobile",
            tenantId = "tenant-live-1",
            branchId = "branch-live-42",
        )

        val repository = buildStoreMobileReceivingRepository(
            pairedDevice = pairedDevice,
            session = session,
        )

        assertTrue(repository is RemoteReceivingRepository)
    }

    @Test
    fun fallsBackToInMemoryReceivingRepositoryWithoutRuntimeSession() {
        val repository = buildStoreMobileReceivingRepository(
            pairedDevice = null,
            session = null,
        )

        assertTrue(repository is InMemoryReceivingRepository)
    }

    @Test
    fun buildsRemoteExpiryRepositoryWhenPairedRuntimeContextExists() {
        val pairedDevice = StoreMobilePairedDevice(
            deviceId = "device-1",
            installationId = "installation-1",
            runtimeProfile = "mobile_store_spoke",
            sessionSurface = "store_mobile",
            hubBaseUrl = "http://10.0.2.2:8000",
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
        )
        val session = StoreMobileRuntimeSession(
            accessToken = "session-token",
            expiresAt = "2026-04-16T10:00:00Z",
            deviceId = "device-1",
            staffProfileId = "staff-1",
            runtimeProfile = "mobile_store_spoke",
            sessionSurface = "store_mobile",
            tenantId = "tenant-live-1",
            branchId = "branch-live-42",
        )

        val repository = buildStoreMobileExpiryRepository(
            pairedDevice = pairedDevice,
            session = session,
        )

        assertTrue(repository is RemoteExpiryRepository)
    }

    @Test
    fun fallsBackToInMemoryExpiryRepositoryWithoutRuntimeSession() {
        val repository = buildStoreMobileExpiryRepository(
            pairedDevice = null,
            session = null,
        )

        assertTrue(repository is InMemoryExpiryRepository)
    }

    @Test
    fun buildsRemoteRestockRepositoryWhenPairedRuntimeContextExists() {
        val pairedDevice = StoreMobilePairedDevice(
            deviceId = "device-1",
            installationId = "installation-1",
            runtimeProfile = "mobile_store_spoke",
            sessionSurface = "store_mobile",
            hubBaseUrl = "http://10.0.2.2:8000",
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
        )
        val session = StoreMobileRuntimeSession(
            accessToken = "session-token",
            expiresAt = "2026-04-16T10:00:00Z",
            deviceId = "device-1",
            staffProfileId = "staff-1",
            runtimeProfile = "mobile_store_spoke",
            sessionSurface = "store_mobile",
            tenantId = "tenant-live-1",
            branchId = "branch-live-42",
        )

        val repository = buildStoreMobileRestockRepository(
            pairedDevice = pairedDevice,
            session = session,
        )

        assertTrue(repository is RemoteRestockRepository)
    }

    @Test
    fun fallsBackToInMemoryRestockRepositoryWithoutRuntimeSession() {
        val repository = buildStoreMobileRestockRepository(
            pairedDevice = null,
            session = null,
        )

        assertTrue(repository is InMemoryRestockRepository)
    }

    @Test
    fun buildsRemoteScanLookupRepositoryWhenPairedRuntimeContextExists() {
        val pairedDevice = StoreMobilePairedDevice(
            deviceId = "device-1",
            installationId = "installation-1",
            runtimeProfile = "mobile_store_spoke",
            sessionSurface = "store_mobile",
            hubBaseUrl = "http://10.0.2.2:8000",
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
        )
        val session = StoreMobileRuntimeSession(
            accessToken = "session-token",
            expiresAt = "2026-04-16T10:00:00Z",
            deviceId = "device-1",
            staffProfileId = "staff-1",
            runtimeProfile = "mobile_store_spoke",
            sessionSurface = "store_mobile",
            tenantId = "tenant-live-1",
            branchId = "branch-live-42",
        )

        val repository = buildStoreMobileScanLookupRepository(
            pairedDevice = pairedDevice,
            session = session,
        )

        assertTrue(repository is RemoteScanLookupRepository)
    }

    @Test
    fun fallsBackToInMemoryScanLookupRepositoryWithoutRuntimeSession() {
        val repository = buildStoreMobileScanLookupRepository(
            pairedDevice = null,
            session = null,
        )

        assertTrue(repository is InMemoryScanLookupRepository)
    }
}
