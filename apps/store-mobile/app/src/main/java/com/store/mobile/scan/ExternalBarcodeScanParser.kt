package com.store.mobile.scan

const val STORE_MOBILE_EXTERNAL_SCAN_ACTION = "com.store.mobile.ACTION_BARCODE_SCAN"

class ExternalBarcodeScanParser(
    private val scanner: CameraBarcodeScanner = CameraBarcodeScanner(),
) {
    fun parse(action: String?, extras: Map<String, String?>): ExternalScannerEvent? {
        if (action != STORE_MOBILE_EXTERNAL_SCAN_ACTION) {
            return null
        }

        val rawValue = extras["com.symbol.datawedge.data_string"]
            ?: extras["barcode"]
            ?: extras["data"]
        val normalized = scanner.normalizeDetectedValue(rawValue)
        return if (normalized == null) {
            ExternalScannerEvent.PayloadError(
                message = "External scanner broadcast did not include a usable barcode payload.",
            )
        } else {
            ExternalScannerEvent.BarcodeDetected(barcode = normalized)
        }
    }
}
