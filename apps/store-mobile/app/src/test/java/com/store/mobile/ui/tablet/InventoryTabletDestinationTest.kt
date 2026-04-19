package com.store.mobile.ui.tablet

import com.store.mobile.ui.operations.MobileOperationsSection
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class InventoryTabletDestinationTest {
    @Test
    fun defaultsTabletRuntimeToOverview() {
        assertEquals(InventoryTabletDestination.OVERVIEW, defaultInventoryTabletDestination())
    }

    @Test
    fun mapsTaskDestinationsToOperationsSections() {
        assertNull(InventoryTabletDestination.OVERVIEW.operationsSection)
        assertEquals(MobileOperationsSection.RECEIVING, InventoryTabletDestination.RECEIVING.operationsSection)
        assertEquals(MobileOperationsSection.STOCK_COUNT, InventoryTabletDestination.STOCK_COUNT.operationsSection)
        assertEquals(MobileOperationsSection.RESTOCK, InventoryTabletDestination.RESTOCK.operationsSection)
        assertEquals(MobileOperationsSection.EXPIRY, InventoryTabletDestination.EXPIRY.operationsSection)
        assertEquals(MobileOperationsSection.SCAN, InventoryTabletDestination.SCAN.operationsSection)
        assertEquals(MobileOperationsSection.RUNTIME, InventoryTabletDestination.RUNTIME.operationsSection)
    }
}
