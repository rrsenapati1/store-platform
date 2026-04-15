package com.store.mobile.scan

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Assert.assertNull
import org.junit.Test

class ZebraDataWedgeConfiguratorTest {
    @Test
    fun detectsInstalledDataWedgePackage() {
        val configurator = ZebraDataWedgeConfigurator()

        assertTrue(
            configurator.isDataWedgeAvailable(
                installedPackages = setOf("com.android.settings", ZebraDataWedgeConfigurator.DATAWEDGE_PACKAGE_NAME),
            ),
        )
        assertFalse(
            configurator.isDataWedgeAvailable(
                installedPackages = setOf("com.android.settings", "com.store.mobile"),
            ),
        )
    }

    @Test
    fun buildsStoreMobileProvisioningCommandForBroadcastOutput() {
        val configurator = ZebraDataWedgeConfigurator()

        val command = configurator.buildProvisioningCommand(
            packageName = "com.store.mobile",
            activityName = "com.store.mobile.MainActivity",
        )

        assertEquals(ZebraDataWedgeConfigurator.DATAWEDGE_API_ACTION, command.action)
        assertEquals(ZebraDataWedgeConfigurator.SET_CONFIG_EXTRA, command.commandExtraKey)
        assertEquals(ZebraDataWedgeConfigurator.STORE_MOBILE_PROFILE_NAME, command.profileName)
        assertEquals("com.store.mobile", command.packageName)
        assertEquals("com.store.mobile.MainActivity", command.activityName)
        assertEquals(STORE_MOBILE_EXTERNAL_SCAN_ACTION, command.intentAction)
        assertEquals(2, command.intentDelivery)
        assertTrue(command.intentOutputEnabled)
        assertFalse(command.keystrokeOutputEnabled)
        assertEquals("LAST_RESULT", command.sendResult)
        assertTrue(command.commandIdentifier.startsWith("store-mobile-dw-"))
    }

    @Test
    fun parsesSuccessfulResultForMatchingProvisioningCommand() {
        val configurator = ZebraDataWedgeConfigurator()

        val result = configurator.parseResult(
            action = ZebraDataWedgeConfigurator.RESULT_ACTION,
            extras = mapOf(
                "COMMAND" to ZebraDataWedgeConfigurator.SET_CONFIG_EXTRA,
                "COMMAND_IDENTIFIER" to "store-mobile-dw-123",
                "RESULT" to "SUCCESS",
            ),
            expectedCommandIdentifier = "store-mobile-dw-123",
        )

        assertEquals(ZebraDataWedgeResult.Configured, result)
    }

    @Test
    fun parsesFailureResultCodeForMatchingProvisioningCommand() {
        val configurator = ZebraDataWedgeConfigurator()

        val result = configurator.parseResult(
            action = ZebraDataWedgeConfigurator.RESULT_ACTION,
            extras = mapOf(
                "COMMAND" to ZebraDataWedgeConfigurator.SET_CONFIG_EXTRA,
                "COMMAND_IDENTIFIER" to "store-mobile-dw-123",
                "RESULT" to "FAILURE",
                "RESULT_CODE" to "PLUGIN_BUNDLE_INVALID",
            ),
            expectedCommandIdentifier = "store-mobile-dw-123",
        )

        require(result is ZebraDataWedgeResult.Error)
        assertEquals("PLUGIN_BUNDLE_INVALID", result.resultCode)
        assertTrue(result.message.contains("PLUGIN_BUNDLE_INVALID"))
    }

    @Test
    fun ignoresUnrelatedResultActionsOrCommandIdentifiers() {
        val configurator = ZebraDataWedgeConfigurator()

        assertNull(
            configurator.parseResult(
                action = "com.store.mobile.UNRELATED",
                extras = mapOf("RESULT" to "SUCCESS"),
                expectedCommandIdentifier = "store-mobile-dw-123",
            ),
        )
        assertNull(
            configurator.parseResult(
                action = ZebraDataWedgeConfigurator.RESULT_ACTION,
                extras = mapOf(
                    "COMMAND" to ZebraDataWedgeConfigurator.SET_CONFIG_EXTRA,
                    "COMMAND_IDENTIFIER" to "different-command",
                    "RESULT" to "SUCCESS",
                ),
                expectedCommandIdentifier = "store-mobile-dw-123",
            ),
        )
    }
}
