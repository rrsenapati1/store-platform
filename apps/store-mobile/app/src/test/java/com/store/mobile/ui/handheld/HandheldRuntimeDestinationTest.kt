package com.store.mobile.ui.handheld

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
}
