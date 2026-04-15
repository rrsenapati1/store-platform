package com.store.mobile

import android.app.Application
import com.store.mobile.scan.ExternalScannerEvent
import com.store.mobile.scan.ZebraDataWedgeResult

class StoreMobileApplication : Application() {
    private val externalBarcodeListeners = linkedSetOf<(ExternalScannerEvent) -> Unit>()
    private val zebraAvailabilityListeners = linkedSetOf<(Boolean) -> Unit>()
    private val zebraResultListeners = linkedSetOf<(ZebraDataWedgeResult) -> Unit>()

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

    fun addZebraAvailabilityListener(listener: (Boolean) -> Unit): () -> Unit {
        zebraAvailabilityListeners += listener
        return {
            zebraAvailabilityListeners -= listener
        }
    }

    fun emitZebraAvailability(isAvailable: Boolean) {
        zebraAvailabilityListeners.toList().forEach { listener ->
            listener(isAvailable)
        }
    }

    fun addZebraResultListener(listener: (ZebraDataWedgeResult) -> Unit): () -> Unit {
        zebraResultListeners += listener
        return {
            zebraResultListeners -= listener
        }
    }

    fun emitZebraResult(result: ZebraDataWedgeResult) {
        zebraResultListeners.toList().forEach { listener ->
            listener(result)
        }
    }
}
