package com.store.mobile.ui.runtime

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test
import com.store.mobile.ui.scan.ScanExternalScannerStatus
import com.store.mobile.ui.scan.ZebraDataWedgeSetupStatus

class RuntimeStatusScreenTest {
    @Test
    fun showsDisconnectedHubState() {
        val state = buildRuntimeStatusState(
            connected = false,
            pendingSyncCount = 0,
        )

        assertFalse(state.connected)
        assertEquals("Disconnected from branch hub", state.title)
    }

    @Test
    fun includesExternalScannerDiagnostics() {
        val state = buildRuntimeStatusState(
            connected = true,
            pendingSyncCount = 2,
            deviceId = "device-1",
            hubBaseUrl = "http://hub.local",
            sessionExpiresAt = "2026-04-15T12:00:00Z",
            externalScannerStatus = ScanExternalScannerStatus.PAYLOAD_ERROR,
            lastExternalScanAt = "2026-04-15T10:00:00Z",
            externalScannerMessage = "Missing barcode payload.",
        )

        assertEquals("External scanner: Scanner payload invalid", state.externalScannerTitle)
        assertEquals("Last external scan: 2026-04-15T10:00:00Z", state.externalScannerLastScanLabel)
        assertEquals("External scanner warning: Missing barcode payload.", state.externalScannerDetail)
    }

    @Test
    fun includesZebraSetupDiagnostics() {
        val state = buildRuntimeStatusState(
            connected = true,
            pendingSyncCount = 2,
            zebraDataWedgeStatus = ZebraDataWedgeSetupStatus.ERROR,
            zebraDataWedgeMessage = "PLUGIN_BUNDLE_INVALID",
        )

        assertEquals("Zebra DataWedge setup failed", state.zebraDataWedgeTitle)
        assertEquals("Zebra setup warning: PLUGIN_BUNDLE_INVALID", state.zebraDataWedgeDetail)
    }
}
