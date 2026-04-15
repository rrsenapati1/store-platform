package com.store.mobile.ui.scan

import com.store.mobile.scan.CameraBarcodeScanner
import com.store.mobile.scan.ScanLookupRepository

enum class ScanCameraStatus {
    CHECKING,
    PERMISSION_REQUIRED,
    READY,
    UNAVAILABLE,
}

enum class ScanLookupSource {
    MANUAL,
    CAMERA,
    EXTERNAL_SCANNER,
}

data class ScanLookupUiState(
    val draftBarcode: String = "",
    val barcode: String = "",
    val productName: String = "",
    val skuCode: String = "",
    val priceLabel: String = "",
    val stockLabel: String = "",
    val availabilityStatus: String = "",
    val cameraStatus: ScanCameraStatus = ScanCameraStatus.CHECKING,
    val cameraMessage: String? = null,
    val lastScanSource: ScanLookupSource = ScanLookupSource.MANUAL,
    val errorMessage: String? = null,
)

class ScanLookupViewModel(
    private val repository: ScanLookupRepository,
    private val scanner: CameraBarcodeScanner = CameraBarcodeScanner(),
) {
    var state: ScanLookupUiState = ScanLookupUiState()
        private set

    fun updateDraftBarcode(value: String) {
        state = state.copy(draftBarcode = value)
    }

    fun setCameraPermission(granted: Boolean) {
        state = state.copy(
            cameraStatus = if (granted) {
                ScanCameraStatus.READY
            } else {
                ScanCameraStatus.PERMISSION_REQUIRED
            },
            cameraMessage = null,
        )
    }

    fun reportCameraUnavailable(message: String) {
        state = state.copy(
            cameraStatus = ScanCameraStatus.UNAVAILABLE,
            cameraMessage = message,
        )
    }

    fun lookupDraftBarcode() {
        lookupNormalizedBarcode(
            rawBarcode = state.draftBarcode,
            source = ScanLookupSource.MANUAL,
        )
    }

    fun lookupScannedBarcode(rawBarcode: String) {
        lookupNormalizedBarcode(
            rawBarcode = rawBarcode,
            source = ScanLookupSource.MANUAL,
        )
    }

    fun onCameraBarcodeDetected(rawBarcode: String, detectedAtMillis: Long) {
        val normalizedBarcode = scanner.consumeDetectedValue(rawBarcode, detectedAtMillis) ?: return
        lookupResolvedBarcode(
            normalizedBarcode = normalizedBarcode,
            source = ScanLookupSource.CAMERA,
        )
    }

    fun onExternalScannerDetected(rawBarcode: String, detectedAtMillis: Long) {
        val normalizedBarcode = scanner.consumeDetectedValue(rawBarcode, detectedAtMillis) ?: return
        lookupResolvedBarcode(
            normalizedBarcode = normalizedBarcode,
            source = ScanLookupSource.EXTERNAL_SCANNER,
        )
    }

    private fun lookupNormalizedBarcode(rawBarcode: String, source: ScanLookupSource) {
        val normalizedBarcode = scanner.normalizeDetectedValue(rawBarcode)
        if (normalizedBarcode == null) {
            state = state.copy(
                barcode = "",
                productName = "",
                skuCode = "",
                priceLabel = "",
                stockLabel = "",
                availabilityStatus = "",
                errorMessage = "Scan a valid barcode to continue.",
                lastScanSource = source,
            )
            return
        }

        lookupResolvedBarcode(normalizedBarcode, source)
    }

    private fun lookupResolvedBarcode(normalizedBarcode: String, source: ScanLookupSource) {
        val record = repository.lookupBarcode(normalizedBarcode)
        if (record == null) {
            state = state.copy(
                draftBarcode = normalizedBarcode,
                barcode = normalizedBarcode,
                productName = "",
                skuCode = "",
                priceLabel = "",
                stockLabel = "",
                availabilityStatus = "",
                lastScanSource = source,
                errorMessage = "No catalog match found for this barcode.",
            )
            return
        }

        state = state.copy(
            draftBarcode = normalizedBarcode,
            barcode = record.barcode,
            productName = record.productName,
            skuCode = record.skuCode,
            priceLabel = "Rs. %.2f".format(record.sellingPrice),
            stockLabel = record.stockOnHand.toInt().toString(),
            availabilityStatus = record.availabilityStatus,
            lastScanSource = source,
            errorMessage = null,
        )
    }
}
