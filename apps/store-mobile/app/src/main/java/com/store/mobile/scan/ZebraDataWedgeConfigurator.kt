package com.store.mobile.scan

import android.content.Intent
import android.os.Bundle

data class ZebraDataWedgeCommand(
    val action: String,
    val commandExtraKey: String,
    val profileName: String,
    val packageName: String,
    val activityName: String,
    val intentAction: String,
    val intentDelivery: Int,
    val intentOutputEnabled: Boolean,
    val keystrokeOutputEnabled: Boolean,
    val sendResult: String,
    val commandIdentifier: String,
)

class ZebraDataWedgeConfigurator {
    fun isDataWedgeAvailable(installedPackages: Set<String>): Boolean {
        return DATAWEDGE_PACKAGE_NAME in installedPackages
    }

    fun buildProvisioningCommand(packageName: String, activityName: String): ZebraDataWedgeCommand {
        return ZebraDataWedgeCommand(
            action = DATAWEDGE_API_ACTION,
            commandExtraKey = SET_CONFIG_EXTRA,
            profileName = STORE_MOBILE_PROFILE_NAME,
            packageName = packageName,
            activityName = activityName,
            intentAction = STORE_MOBILE_EXTERNAL_SCAN_ACTION,
            intentDelivery = INTENT_DELIVERY_BROADCAST,
            intentOutputEnabled = true,
            keystrokeOutputEnabled = false,
            sendResult = SEND_RESULT_LAST,
            commandIdentifier = "store-mobile-dw-${System.currentTimeMillis()}",
        )
    }

    fun buildProvisioningIntent(command: ZebraDataWedgeCommand): Intent {
        val profileConfig = Bundle().apply {
            putString("PROFILE_NAME", command.profileName)
            putString("PROFILE_ENABLED", "true")
            putString("CONFIG_MODE", "CREATE_IF_NOT_EXIST")
            putParcelableArrayList("APP_LIST", arrayListOf(
                Bundle().apply {
                    putString("PACKAGE_NAME", command.packageName)
                    putStringArrayList("ACTIVITY_LIST", arrayListOf(command.activityName, "*"))
                },
            ))

            val pluginConfigs = arrayListOf(
                Bundle().apply {
                    putString("PLUGIN_NAME", "INTENT")
                    putString("RESET_CONFIG", "true")
                    putBundle("PARAM_LIST", Bundle().apply {
                        putString("intent_output_enabled", command.intentOutputEnabled.toString())
                        putString("intent_action", command.intentAction)
                        putString("intent_category", "android.intent.category.DEFAULT")
                        putString("intent_delivery", command.intentDelivery.toString())
                    })
                },
                Bundle().apply {
                    putString("PLUGIN_NAME", "KEYSTROKE")
                    putString("RESET_CONFIG", "true")
                    putBundle("PARAM_LIST", Bundle().apply {
                        putString("keystroke_output_enabled", command.keystrokeOutputEnabled.toString())
                    })
                },
            )
            putParcelableArrayList("PLUGIN_CONFIG", pluginConfigs)
        }

        return Intent(command.action).apply {
            putExtra(command.commandExtraKey, profileConfig)
            putExtra("SEND_RESULT", command.sendResult)
            putExtra("COMMAND_IDENTIFIER", command.commandIdentifier)
        }
    }

    fun parseResult(
        action: String?,
        extras: Map<String, String?>,
        expectedCommandIdentifier: String,
    ): ZebraDataWedgeResult? {
        if (action != RESULT_ACTION) {
            return null
        }
        if (extras["COMMAND"] != SET_CONFIG_EXTRA) {
            return null
        }
        if (extras["COMMAND_IDENTIFIER"] != expectedCommandIdentifier) {
            return null
        }

        return when (extras["RESULT"]) {
            "SUCCESS" -> ZebraDataWedgeResult.Configured
            "FAILURE" -> {
                val resultCode = extras["RESULT_CODE"]
                ZebraDataWedgeResult.Error(
                    message = if (resultCode.isNullOrBlank()) {
                        "DataWedge rejected the Store Mobile provisioning command."
                    } else {
                        "DataWedge rejected the Store Mobile provisioning command: $resultCode"
                    },
                    resultCode = resultCode,
                )
            }

            else -> ZebraDataWedgeResult.Error(
                message = "DataWedge returned an unknown provisioning result.",
                resultCode = extras["RESULT_CODE"],
            )
        }
    }

    companion object {
        const val DATAWEDGE_PACKAGE_NAME = "com.symbol.datawedge"
        const val DATAWEDGE_API_ACTION = "com.symbol.datawedge.api.ACTION"
        const val SET_CONFIG_EXTRA = "com.symbol.datawedge.api.SET_CONFIG"
        const val RESULT_ACTION = "com.symbol.datawedge.api.RESULT_ACTION"
        const val STORE_MOBILE_PROFILE_NAME = "Store Mobile"
        const val SEND_RESULT_LAST = "LAST_RESULT"
        const val INTENT_DELIVERY_BROADCAST = 2
    }
}
