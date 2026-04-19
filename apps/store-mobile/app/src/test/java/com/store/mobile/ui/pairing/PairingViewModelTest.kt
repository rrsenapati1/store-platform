package com.store.mobile.ui.pairing

import com.store.mobile.runtime.FakeStoreMobileHubClient
import com.store.mobile.runtime.InMemoryStoreMobileKeyValueStore
import com.store.mobile.runtime.StoreMobilePersistentPairingRepository
import com.store.mobile.runtime.StoreMobileRuntimeSession
import com.store.mobile.runtime.StoreMobilePersistentSessionRepository
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class PairingViewModelTest {
    @Test
    fun exposesManualActivationReadyState() {
        val keyValueStore = InMemoryStoreMobileKeyValueStore()
        val viewModel = PairingViewModel(
            pairingRepository = StoreMobilePersistentPairingRepository(keyValueStore),
            sessionRepository = StoreMobilePersistentSessionRepository(keyValueStore),
            hubClient = FakeStoreMobileHubClient(),
        )

        viewModel.updateManualActivation(
            hubBaseUrl = "http://127.0.0.1:9400",
            activationCode = "ABCD-1234-EFGH",
        )

        assertEquals("http://127.0.0.1:9400", viewModel.state.hubBaseUrl)
        assertEquals("ABCD-1234-EFGH", viewModel.state.activationCode)
        assertTrue(viewModel.state.canRedeemActivation)
        assertNull(viewModel.state.pairedDevice)
    }

    @Test
    fun redeemsInventoryTabletActivationIntoPairedTabletDevice() {
        val keyValueStore = InMemoryStoreMobileKeyValueStore()
        val viewModel = PairingViewModel(
            pairingRepository = StoreMobilePersistentPairingRepository(keyValueStore),
            sessionRepository = StoreMobilePersistentSessionRepository(keyValueStore),
            hubClient = FakeStoreMobileHubClient(),
        )

        viewModel.updateManualActivation(
            hubBaseUrl = "http://127.0.0.1:9400",
            activationCode = "TABL-1234-EFGH",
        )
        viewModel.updateRequestedSessionSurface("inventory_tablet")
        viewModel.redeemManualActivation(installationId = "android-tablet-installation")

        assertEquals("inventory_tablet", viewModel.state.requestedSessionSurface)
        assertEquals("inventory_tablet_spoke", viewModel.state.pairedDevice?.runtimeProfile)
        assertEquals("inventory_tablet", viewModel.state.pairedDevice?.sessionSurface)
        assertEquals("tenant-demo-1", viewModel.state.pairedDevice?.tenantId)
        assertEquals("branch-demo-1", viewModel.state.pairedDevice?.branchId)
    }

    @Test
    fun persistsRuntimeSessionWithTenantAndBranchContext() {
        val keyValueStore = InMemoryStoreMobileKeyValueStore()
        val sessionRepository = StoreMobilePersistentSessionRepository(keyValueStore)
        val viewModel = PairingViewModel(
            pairingRepository = StoreMobilePersistentPairingRepository(keyValueStore),
            sessionRepository = sessionRepository,
            hubClient = FakeStoreMobileHubClient(),
        )

        viewModel.updateManualActivation(
            hubBaseUrl = "http://127.0.0.1:9400",
            activationCode = "MOBI-1234-EFGH",
        )
        viewModel.redeemManualActivation(installationId = "android-handheld-installation")

        assertEquals("tenant-demo-1", sessionRepository.loadSession()?.tenantId)
        assertEquals("branch-demo-1", sessionRepository.loadSession()?.branchId)
    }

    @Test
    fun restoresSignedOutStateForPersistedPairingWithoutSession() {
        val keyValueStore = InMemoryStoreMobileKeyValueStore()
        val pairingRepository = StoreMobilePersistentPairingRepository(keyValueStore)
        pairingRepository.savePairedDevice(
            deviceId = "paired-mobile-1",
            installationId = "android-installation-demo",
            runtimeProfile = "mobile_store_spoke",
            sessionSurface = "store_mobile",
            hubBaseUrl = "http://127.0.0.1:9400",
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
        )

        val viewModel = PairingViewModel(
            pairingRepository = pairingRepository,
            sessionRepository = StoreMobilePersistentSessionRepository(keyValueStore),
            hubClient = FakeStoreMobileHubClient(),
        )

        assertEquals(PairingSessionStatus.SIGNED_OUT, viewModel.state.sessionStatus)
        assertEquals("http://127.0.0.1:9400", viewModel.state.hubBaseUrl)
    }

    @Test
    fun signsOutWithoutDroppingPersistedPairing() {
        val keyValueStore = InMemoryStoreMobileKeyValueStore()
        val pairingRepository = StoreMobilePersistentPairingRepository(keyValueStore)
        val sessionRepository = StoreMobilePersistentSessionRepository(keyValueStore)
        val viewModel = PairingViewModel(
            pairingRepository = pairingRepository,
            sessionRepository = sessionRepository,
            hubClient = FakeStoreMobileHubClient(),
        )

        viewModel.updateManualActivation(
            hubBaseUrl = "http://127.0.0.1:9400",
            activationCode = "MOBI-1234-EFGH",
        )
        viewModel.redeemManualActivation(installationId = "android-handheld-installation")
        viewModel.signOutSession()

        assertEquals(PairingSessionStatus.SIGNED_OUT, viewModel.state.sessionStatus)
        assertEquals("paired-mobile-1", viewModel.state.pairedDevice?.deviceId)
        assertNull(sessionRepository.loadSession())
    }

    @Test
    fun clearsExpiredPersistedSessionOnRestore() {
        val keyValueStore = InMemoryStoreMobileKeyValueStore()
        val pairingRepository = StoreMobilePersistentPairingRepository(keyValueStore)
        val sessionRepository = StoreMobilePersistentSessionRepository(keyValueStore)
        pairingRepository.savePairedDevice(
            deviceId = "paired-mobile-1",
            installationId = "android-installation-demo",
            runtimeProfile = "mobile_store_spoke",
            sessionSurface = "store_mobile",
            hubBaseUrl = "http://127.0.0.1:9400",
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
        )
        sessionRepository.saveSession(
            StoreMobileRuntimeSession(
                accessToken = "expired-session",
                expiresAt = "2000-01-01T00:00:00Z",
                deviceId = "paired-mobile-1",
                staffProfileId = "staff-demo-1",
                runtimeProfile = "mobile_store_spoke",
                sessionSurface = "store_mobile",
                tenantId = "tenant-demo-1",
                branchId = "branch-demo-1",
            ),
        )

        val viewModel = PairingViewModel(
            pairingRepository = pairingRepository,
            sessionRepository = sessionRepository,
            hubClient = FakeStoreMobileHubClient(),
        )

        assertEquals(PairingSessionStatus.EXPIRED, viewModel.state.sessionStatus)
        assertNull(sessionRepository.loadSession())
    }
}
