package com.store.mobile.ui.handheld

import com.store.mobile.ui.operations.MobileOperationsSection
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class HandheldRuntimeDestinationTest {
    @Test
    fun exposesOnlyLiveHandheldRuntimeDestinations() {
        assertEquals(
            listOf("SCAN", "TASKS", "RUNTIME"),
            HandheldRuntimeDestination.entries.map { it.name },
        )
    }

    @Test
    fun keepsEntryOutsideTheLiveRuntimeShell() {
        assertFalse(HandheldRuntimeDestination.entries.any { it.name == "ENTRY" })
    }

    @Test
    fun mapsLegacyOperationSectionsIntoRuntimeDestinations() {
        assertEquals(HandheldRuntimeDestination.SCAN, resolveHandheldRuntimeDestination(MobileOperationsSection.SCAN))
        assertEquals(HandheldRuntimeDestination.TASKS, resolveHandheldRuntimeDestination(MobileOperationsSection.RECEIVING))
        assertEquals(HandheldRuntimeDestination.TASKS, resolveHandheldRuntimeDestination(MobileOperationsSection.STOCK_COUNT))
        assertEquals(HandheldRuntimeDestination.TASKS, resolveHandheldRuntimeDestination(MobileOperationsSection.RESTOCK))
        assertEquals(HandheldRuntimeDestination.TASKS, resolveHandheldRuntimeDestination(MobileOperationsSection.EXPIRY))
        assertEquals(HandheldRuntimeDestination.RUNTIME, resolveHandheldRuntimeDestination(MobileOperationsSection.RUNTIME))
    }
}
