package com.store.mobile.ui.pairing

import com.store.mobile.runtime.FakeStoreMobileHubClient
import com.store.mobile.runtime.InMemoryStoreMobilePairingRepository
import com.store.mobile.runtime.InMemoryStoreMobileSessionRepository
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class PairingViewModelTest {
    @Test
    fun exposesManualActivationReadyState() {
        val viewModel = PairingViewModel(
            pairingRepository = InMemoryStoreMobilePairingRepository(),
            sessionRepository = InMemoryStoreMobileSessionRepository(),
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
        val viewModel = PairingViewModel(
            pairingRepository = InMemoryStoreMobilePairingRepository(),
            sessionRepository = InMemoryStoreMobileSessionRepository(),
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
    }
}
