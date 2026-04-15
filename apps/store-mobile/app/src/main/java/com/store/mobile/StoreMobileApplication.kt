package com.store.mobile

import android.app.Application

class StoreMobileApplication : Application() {
    private val externalBarcodeListeners = linkedSetOf<(String) -> Unit>()

    fun addExternalBarcodeListener(listener: (String) -> Unit): () -> Unit {
        externalBarcodeListeners += listener
        return {
            externalBarcodeListeners -= listener
        }
    }

    fun emitExternalBarcode(barcode: String) {
        externalBarcodeListeners.toList().forEach { listener ->
            listener(barcode)
        }
    }
}
