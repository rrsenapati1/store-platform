package com.store.mobile.ui.entry

import com.store.mobile.runtime.StoreMobilePairedDevice
import com.store.mobile.ui.pairing.PairingSessionStatus
import com.store.mobile.ui.pairing.PairingUiState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class StoreMobileEntrySurfaceModelTest {
    @Test
    fun expiredSessionProducesRecoveryFocusedEntryPosture() {
        val model = buildStoreMobileEntryStatusModel(
            PairingUiState(
                pairedDevice = pairedHandheld(),
                sessionStatus = PairingSessionStatus.EXPIRED,
                errorMessage = "Runtime session expired. Redeem a fresh activation or unpair this device.",
            ),
        )

        assertEquals("Session recovery", model.eyebrow)
        assertEquals("Recover this paired runtime", model.title)
        assertTrue(model.detail.contains("expired"))
        assertEquals(
            "Redeem a fresh activation or unpair this device before returning to handheld work.",
            model.actionHint,
        )
    }

    @Test
    fun unpairedDeviceProducesActivationEntryPosture() {
        val model = buildStoreMobileEntryStatusModel(
            PairingUiState(
                sessionStatus = PairingSessionStatus.UNPAIRED,
            ),
        )

        assertEquals("Activation required", model.eyebrow)
        assertEquals("Pair this device to a branch hub", model.title)
        assertTrue(model.detail.contains("approved branch hub"))
        assertEquals(
            "Choose handheld or inventory tablet mode, then redeem the activation your owner approved for this device.",
            model.actionHint,
        )
    }

    private fun pairedHandheld(): StoreMobilePairedDevice {
        return StoreMobilePairedDevice(
            deviceId = "device-1",
            installationId = "install-1",
            runtimeProfile = "handheld",
            sessionSurface = "store_mobile",
            hubBaseUrl = "http://hub.local",
            tenantId = "tenant-1",
            branchId = "branch-1",
        )
    }
}
