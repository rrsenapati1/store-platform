package com.store.mobile.ui.theme

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class StoreMobileThemeModeTest {
    @Test
    fun exposesAllSupportedThemeModes() {
        assertEquals(
            listOf("SYSTEM", "LIGHT", "DARK"),
            StoreMobileThemeMode.entries.map { it.name },
        )
    }

    @Test
    fun reportsWhetherThemeModeIsSystemManaged() {
        assertTrue(StoreMobileThemeMode.SYSTEM.usesSystemSetting)
        assertEquals(false, StoreMobileThemeMode.LIGHT.usesSystemSetting)
        assertEquals(false, StoreMobileThemeMode.DARK.usesSystemSetting)
    }
}
