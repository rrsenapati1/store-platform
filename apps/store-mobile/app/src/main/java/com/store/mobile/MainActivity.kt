package com.store.mobile

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.core.content.ContextCompat
import com.store.mobile.scan.ExternalBarcodeScanParser
import com.store.mobile.ui.StoreMobileApp

class MainActivity : ComponentActivity() {
    private val externalScanParser = ExternalBarcodeScanParser()
    private val externalScannerReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            handleExternalScannerIntent(intent)
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
    }

    override fun onStop() {
        unregisterReceiver(externalScannerReceiver)
        super.onStop()
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
}
