package com.store.mobile.scan

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class ExternalBarcodeScanParserTest {
    @Test
    fun parsesConfiguredDataWedgePayload() {
        val parser = ExternalBarcodeScanParser()

        val barcode = parser.parse(
            action = STORE_MOBILE_EXTERNAL_SCAN_ACTION,
            extras = mapOf("com.symbol.datawedge.data_string" to " 1234 5678 90123 "),
        )

        assertEquals("1234567890123", barcode)
    }

    @Test
    fun acceptsFallbackBarcodeExtraForCompatibleScanners() {
        val parser = ExternalBarcodeScanParser()

        val barcode = parser.parse(
            action = STORE_MOBILE_EXTERNAL_SCAN_ACTION,
            extras = mapOf("barcode" to " SKU-001 "),
        )

        assertEquals("SKU-001", barcode)
    }

    @Test
    fun ignoresUnknownScannerActions() {
        val parser = ExternalBarcodeScanParser()

        val barcode = parser.parse(
            action = "com.store.mobile.UNRELATED",
            extras = mapOf("com.symbol.datawedge.data_string" to "1234567890123"),
        )

        assertNull(barcode)
    }
}
