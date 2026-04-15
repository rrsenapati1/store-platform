package com.store.mobile

import android.app.Application
import com.store.mobile.scan.ExternalScannerEvent

class StoreMobileApplication : Application() {
    private val externalBarcodeListeners = linkedSetOf<(ExternalScannerEvent) -> Unit>()

    fun addExternalBarcodeListener(listener: (ExternalScannerEvent) -> Unit): () -> Unit {
        externalBarcodeListeners += listener
        return {
            externalBarcodeListeners -= listener
        }
    }

    fun emitExternalBarcode(event: ExternalScannerEvent) {
        externalBarcodeListeners.toList().forEach { listener ->
            listener(event)
        }
    }
}
