package com.store.mobile

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Bundle
import android.content.pm.PackageManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.core.content.ContextCompat
import com.store.mobile.scan.ExternalBarcodeScanParser
import com.store.mobile.scan.ZebraDataWedgeConfigurator
import com.store.mobile.ui.StoreMobileApp

class MainActivity : ComponentActivity() {
    private val externalScanParser = ExternalBarcodeScanParser()
    private val zebraConfigurator = ZebraDataWedgeConfigurator()
    private var pendingZebraCommandIdentifier: String? = null
    private val externalScannerReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            handleExternalScannerIntent(intent)
        }
    }
    private val zebraResultReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            handleZebraResultIntent(intent)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            StoreMobileApp()
        }
    }

    override fun onStart() {
        super.onStart()
        ContextCompat.registerReceiver(
            this,
            externalScannerReceiver,
            IntentFilter(com.store.mobile.scan.STORE_MOBILE_EXTERNAL_SCAN_ACTION),
            ContextCompat.RECEIVER_NOT_EXPORTED,
        )
        ContextCompat.registerReceiver(
            this,
            zebraResultReceiver,
            IntentFilter(ZebraDataWedgeConfigurator.RESULT_ACTION),
            ContextCompat.RECEIVER_NOT_EXPORTED,
        )
        publishZebraAvailability()
    }

    override fun onStop() {
        unregisterReceiver(zebraResultReceiver)
        unregisterReceiver(externalScannerReceiver)
        super.onStop()
    }

    fun configureZebraDataWedge() {
        if (!isZebraDataWedgeAvailable()) {
            publishZebraAvailability()
            return
        }
        val command = zebraConfigurator.buildProvisioningCommand(
            packageName = packageName,
            activityName = componentName.className,
        )
        pendingZebraCommandIdentifier = command.commandIdentifier
        sendBroadcast(zebraConfigurator.buildProvisioningIntent(command))
    }

    private fun handleExternalScannerIntent(intent: Intent?) {
        val extras = intent?.extras?.keySet()?.associateWith { key ->
            intent.extras?.getString(key)
        }.orEmpty()
        val barcode = externalScanParser.parse(
            action = intent?.action,
            extras = extras,
        ) ?: return
        (application as? StoreMobileApplication)?.emitExternalBarcode(barcode)
    }

    private fun handleZebraResultIntent(intent: Intent?) {
        val expectedCommandIdentifier = pendingZebraCommandIdentifier ?: return
        val result = zebraConfigurator.parseResult(
            action = intent?.action,
            extras = flattenIntentExtras(intent),
            expectedCommandIdentifier = expectedCommandIdentifier,
        ) ?: return
        pendingZebraCommandIdentifier = null
        (application as? StoreMobileApplication)?.emitZebraResult(result)
    }

    private fun publishZebraAvailability() {
        (application as? StoreMobileApplication)?.emitZebraAvailability(isZebraDataWedgeAvailable())
    }

    @Suppress("DEPRECATION")
    private fun isZebraDataWedgeAvailable(): Boolean {
        return try {
            packageManager.getPackageInfo(ZebraDataWedgeConfigurator.DATAWEDGE_PACKAGE_NAME, 0)
            true
        } catch (_: PackageManager.NameNotFoundException) {
            false
        }
    }

    private fun flattenIntentExtras(intent: Intent?): Map<String, String?> {
        val extras = mutableMapOf<String, String?>()
        val intentExtras = intent?.extras ?: return extras
        intentExtras.keySet().forEach { key ->
            when (val nestedBundle = intentExtras.getBundle(key)) {
                is Bundle -> {
                    nestedBundle.keySet().forEach { nestedKey ->
                        extras[nestedKey] = nestedBundle.getString(nestedKey)
                    }
                }

                null -> extras[key] = intentExtras.getString(key)
            }
        }
        return extras
    }
}
