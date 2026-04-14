package com.store.mobile.scan

class CameraBarcodeScanner {
    fun normalizeDetectedValue(rawValue: String?): String? {
        val normalized = rawValue.orEmpty().replace("\\s+".toRegex(), "").trim()
        return normalized.ifBlank { null }
    }
}
