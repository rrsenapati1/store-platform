package com.store.mobile.scan

const val STORE_MOBILE_EXTERNAL_SCAN_ACTION = "com.store.mobile.ACTION_BARCODE_SCAN"

class ExternalBarcodeScanParser(
    private val scanner: CameraBarcodeScanner = CameraBarcodeScanner(),
) {
    fun parse(action: String?, extras: Map<String, String?>): String? {
        if (action != STORE_MOBILE_EXTERNAL_SCAN_ACTION) {
            return null
        }

        val rawValue = extras["com.symbol.datawedge.data_string"]
            ?: extras["barcode"]
            ?: extras["data"]

        return scanner.normalizeDetectedValue(rawValue)
    }
}
