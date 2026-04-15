package com.store.mobile.scan

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Assert.assertNull
import org.junit.Test

class ExternalBarcodeScanParserTest {
    @Test
    fun parsesConfiguredDataWedgePayload() {
        val parser = ExternalBarcodeScanParser()

        val result = parser.parse(
            action = STORE_MOBILE_EXTERNAL_SCAN_ACTION,
            extras = mapOf("com.symbol.datawedge.data_string" to " 1234 5678 90123 "),
        )

        require(result is ExternalScannerEvent.BarcodeDetected)
        assertEquals("1234567890123", result.barcode)
    }

    @Test
    fun acceptsFallbackBarcodeExtraForCompatibleScanners() {
        val parser = ExternalBarcodeScanParser()

        val result = parser.parse(
            action = STORE_MOBILE_EXTERNAL_SCAN_ACTION,
            extras = mapOf("barcode" to " SKU-001 "),
        )

        require(result is ExternalScannerEvent.BarcodeDetected)
        assertEquals("SKU-001", result.barcode)
    }

    @Test
    fun reportsPayloadErrorWhenConfiguredActionHasNoUsableBarcode() {
        val parser = ExternalBarcodeScanParser()

        val result = parser.parse(
            action = STORE_MOBILE_EXTERNAL_SCAN_ACTION,
            extras = mapOf("com.symbol.datawedge.data_string" to "   "),
        )

        require(result is ExternalScannerEvent.PayloadError)
        assertTrue(result.message.contains("usable barcode"))
    }

    @Test
    fun ignoresUnknownScannerActions() {
        val parser = ExternalBarcodeScanParser()

        val result = parser.parse(
            action = "com.store.mobile.UNRELATED",
            extras = mapOf("com.symbol.datawedge.data_string" to "1234567890123"),
        )

        assertNull(result)
    }
}
