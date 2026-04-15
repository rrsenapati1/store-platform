package com.store.mobile.scan

sealed interface ExternalScannerEvent {
    data class BarcodeDetected(
        val barcode: String,
        val detectedAtMillis: Long = System.currentTimeMillis(),
    ) : ExternalScannerEvent

    data class PayloadError(
        val message: String,
        val detectedAtMillis: Long = System.currentTimeMillis(),
    ) : ExternalScannerEvent
}
