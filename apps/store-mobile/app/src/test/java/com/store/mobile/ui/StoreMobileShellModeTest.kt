package com.store.mobile.ui

import org.junit.Assert.assertEquals
import org.junit.Test

class StoreMobileShellModeTest {
    @Test
    fun resolvesTabletShellForInventoryTabletRuntimeProfile() {
        assertEquals(
            StoreMobileShellMode.TABLET,
            resolveStoreMobileShellMode(runtimeProfile = "inventory_tablet_spoke"),
        )
    }
}
