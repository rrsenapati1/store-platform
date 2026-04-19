package com.store.mobile

import com.store.mobile.ui.theme.StoreMobileThemeMode
import org.junit.Assert.assertEquals
import org.junit.Test

class StoreMobileAppBootstrapTest {
    @Test
    fun exposesMobileRuntimeAppName() {
        assertEquals("Store Mobile", StoreMobileAppBootstrap.appName)
    }

    @Test
    fun defaultsToSystemThemeMode() {
        assertEquals(StoreMobileThemeMode.SYSTEM, StoreMobileAppBootstrap.defaultThemeMode)
    }
}
