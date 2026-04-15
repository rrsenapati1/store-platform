package com.store.mobile.scan

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class CameraBarcodeScannerTest {
    @Test
    fun normalizesDetectedValues() {
        val scanner = CameraBarcodeScanner()

        assertEquals("1234567890123", scanner.normalizeDetectedValue(" 1234 5678 90123 "))
        assertNull(scanner.normalizeDetectedValue("   "))
    }

    @Test
    fun suppressesDuplicateDetectionsInsideCooldownWindow() {
        val scanner = CameraBarcodeScanner(duplicateCooldownMs = 1_500L)

        val first = scanner.consumeDetectedValue("1234567890123", detectedAtMillis = 10_000L)
        val duplicate = scanner.consumeDetectedValue("1234567890123", detectedAtMillis = 10_900L)

        assertEquals("1234567890123", first)
        assertNull(duplicate)
    }

    @Test
    fun acceptsRepeatedBarcodeAfterCooldownExpires() {
        val scanner = CameraBarcodeScanner(duplicateCooldownMs = 1_500L)

        scanner.consumeDetectedValue("1234567890123", detectedAtMillis = 10_000L)

        val accepted = scanner.consumeDetectedValue("1234567890123", detectedAtMillis = 11_600L)

        assertEquals("1234567890123", accepted)
    }
}
