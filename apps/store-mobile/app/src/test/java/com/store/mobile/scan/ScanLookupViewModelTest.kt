package com.store.mobile.scan

import com.store.mobile.ui.scan.ScanLookupViewModel
import org.junit.Assert.assertEquals
import org.junit.Test

class ScanLookupViewModelTest {
    @Test
    fun resolvesScannedBarcodeIntoLookupState() {
        val repository = InMemoryScanLookupRepository(
            records = listOf(
                ScanLookupRecord(
                    productId = "prod-1",
                    productName = "ACME TEA",
                    skuCode = "TEA-001",
                    barcode = "1234567890123",
                    sellingPrice = 125.0,
                    stockOnHand = 18.0,
                    availabilityStatus = "IN_STOCK",
                ),
            ),
        )
        val viewModel = ScanLookupViewModel(repository)

        viewModel.lookupScannedBarcode(" 1234567890123 ")

        assertEquals("ACME TEA", viewModel.state.productName)
        assertEquals("1234567890123", viewModel.state.barcode)
        assertEquals("18", viewModel.state.stockLabel)
    }
}
