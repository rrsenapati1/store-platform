package com.store.mobile.ui

import org.junit.Assert.assertEquals
import org.junit.Test
import com.store.mobile.ui.tablet.InventoryTabletDestination
import com.store.mobile.ui.tablet.defaultInventoryTabletDestination

class StoreMobileShellModeTest {
    @Test
    fun resolvesTabletShellForInventoryTabletRuntimeProfile() {
        assertEquals(
            StoreMobileShellMode.TABLET,
            resolveStoreMobileShellMode(runtimeProfile = "inventory_tablet_spoke"),
        )
    }

    @Test
    fun inventoryTabletDefaultDestinationIsOverview() {
        assertEquals(InventoryTabletDestination.OVERVIEW, defaultInventoryTabletDestination())
    }
}
