package com.store.mobile.ui.runtime

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

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
}
