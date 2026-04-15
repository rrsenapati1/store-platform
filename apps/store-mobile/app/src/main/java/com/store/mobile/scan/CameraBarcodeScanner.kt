package com.store.mobile.scan

class CameraBarcodeScanner(
    private val duplicateCooldownMs: Long = 1_500L,
) {
    private var lastAcceptedBarcode: String? = null
    private var lastAcceptedAtMillis: Long = Long.MIN_VALUE

    fun normalizeDetectedValue(rawValue: String?): String? {
        val normalized = rawValue.orEmpty().replace("\\s+".toRegex(), "").trim()
        return normalized.ifBlank { null }
    }

    fun consumeDetectedValue(rawValue: String?, detectedAtMillis: Long): String? {
        val normalized = normalizeDetectedValue(rawValue) ?: return null
        if (
            normalized == lastAcceptedBarcode &&
            detectedAtMillis - lastAcceptedAtMillis < duplicateCooldownMs
        ) {
            return null
        }

        lastAcceptedBarcode = normalized
        lastAcceptedAtMillis = detectedAtMillis
        return normalized
    }
}
