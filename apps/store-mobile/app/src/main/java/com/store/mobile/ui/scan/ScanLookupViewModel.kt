package com.store.mobile.ui.scan

import com.store.mobile.scan.CameraBarcodeScanner
import com.store.mobile.scan.ScanLookupRepository

data class ScanLookupUiState(
    val barcode: String = "",
    val productName: String = "",
    val skuCode: String = "",
    val priceLabel: String = "",
    val stockLabel: String = "",
    val availabilityStatus: String = "",
    val errorMessage: String? = null,
)

class ScanLookupViewModel(
    private val repository: ScanLookupRepository,
    private val scanner: CameraBarcodeScanner = CameraBarcodeScanner(),
) {
    var state: ScanLookupUiState = ScanLookupUiState()
        private set

    fun lookupScannedBarcode(rawBarcode: String) {
        val normalizedBarcode = scanner.normalizeDetectedValue(rawBarcode)
        if (normalizedBarcode == null) {
            state = ScanLookupUiState(errorMessage = "Scan a valid barcode to continue.")
            return
        }

        val record = repository.lookupBarcode(normalizedBarcode)
        if (record == null) {
            state = ScanLookupUiState(
                barcode = normalizedBarcode,
                errorMessage = "No catalog match found for this barcode.",
            )
            return
        }

        state = ScanLookupUiState(
            barcode = record.barcode,
            productName = record.productName,
            skuCode = record.skuCode,
            priceLabel = "Rs. %.2f".format(record.sellingPrice),
            stockLabel = record.stockOnHand.toInt().toString(),
            availabilityStatus = record.availabilityStatus,
            errorMessage = null,
        )
    }
}
