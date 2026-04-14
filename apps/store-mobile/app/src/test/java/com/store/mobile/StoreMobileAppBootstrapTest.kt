package com.store.mobile

import org.junit.Assert.assertEquals
import org.junit.Test

class StoreMobileAppBootstrapTest {
    @Test
    fun exposesMobileRuntimeAppName() {
        assertEquals("Store Mobile", StoreMobileAppBootstrap.appName)
    }
}
