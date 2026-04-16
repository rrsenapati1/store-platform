package com.store.mobile.ui.scan

import com.store.mobile.scan.CameraBarcodeScanner
import com.store.mobile.scan.ScanLookupRepository
import com.store.mobile.scan.ZebraDataWedgeResult
import java.time.Instant

enum class ScanCameraStatus {
    CHECKING,
    PERMISSION_REQUIRED,
    READY,
    UNAVAILABLE,
}

enum class ScanExternalScannerStatus {
    UNCONFIGURED,
    READY,
    RECENT_SCAN,
    PAYLOAD_ERROR,
}

enum class ScanLookupSource {
    MANUAL,
    CAMERA,
    EXTERNAL_SCANNER,
}

enum class ZebraDataWedgeSetupStatus {
    UNAVAILABLE,
    AVAILABLE,
    APPLYING,
    CONFIGURED,
    ERROR,
}

data class ScanLookupUiState(
    val productId: String? = null,
    val draftBarcode: String = "",
    val barcode: String = "",
    val productName: String = "",
    val skuCode: String = "",
    val priceLabel: String = "",
    val stockLabel: String = "",
    val stockOnHand: Double? = null,
    val reorderPoint: Double? = null,
    val targetStock: Double? = null,
    val availabilityStatus: String = "",
    val cameraStatus: ScanCameraStatus = ScanCameraStatus.CHECKING,
    val cameraMessage: String? = null,
    val externalScannerStatus: ScanExternalScannerStatus = ScanExternalScannerStatus.UNCONFIGURED,
    val externalScannerMessage: String? = null,
    val lastExternalScanAt: String? = null,
    val zebraDataWedgeStatus: ZebraDataWedgeSetupStatus = ZebraDataWedgeSetupStatus.UNAVAILABLE,
    val zebraDataWedgeMessage: String? = null,
    val lastScanSource: ScanLookupSource = ScanLookupSource.MANUAL,
    val errorMessage: String? = null,
)

class ScanLookupViewModel(
    private val repository: ScanLookupRepository,
    private val scanner: CameraBarcodeScanner = CameraBarcodeScanner(),
) {
    private var hasValidatedExternalScanner = false
    private var lastExternalScanAtMillis: Long? = null

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
        hasValidatedExternalScanner = true
        lastExternalScanAtMillis = detectedAtMillis
        lookupResolvedBarcode(
            normalizedBarcode = normalizedBarcode,
            source = ScanLookupSource.EXTERNAL_SCANNER,
        )
        state = state.copy(
            externalScannerStatus = ScanExternalScannerStatus.RECENT_SCAN,
            externalScannerMessage = null,
            lastExternalScanAt = Instant.ofEpochMilli(detectedAtMillis).toString(),
        )
    }

    fun reportExternalScannerPayloadError(message: String, detectedAtMillis: Long = System.currentTimeMillis()) {
        state = state.copy(
            externalScannerStatus = ScanExternalScannerStatus.PAYLOAD_ERROR,
            externalScannerMessage = message,
            lastExternalScanAt = state.lastExternalScanAt,
        )
        if (lastExternalScanAtMillis == null) {
            lastExternalScanAtMillis = detectedAtMillis
        }
    }

    fun refreshExternalScannerStatus(referenceTimeMillis: Long) {
        val lastScan = lastExternalScanAtMillis
        if (
            state.externalScannerStatus == ScanExternalScannerStatus.RECENT_SCAN &&
            lastScan != null &&
            referenceTimeMillis - lastScan >= EXTERNAL_SCANNER_RECENT_WINDOW_MS
        ) {
            state = state.copy(
                externalScannerStatus = if (hasValidatedExternalScanner) {
                    ScanExternalScannerStatus.READY
                } else {
                    ScanExternalScannerStatus.UNCONFIGURED
                },
            )
        }
    }

    fun updateZebraDataWedgeAvailability(isAvailable: Boolean) {
        state = state.copy(
            zebraDataWedgeStatus = when {
                !isAvailable -> ZebraDataWedgeSetupStatus.UNAVAILABLE
                state.zebraDataWedgeStatus == ZebraDataWedgeSetupStatus.CONFIGURED -> ZebraDataWedgeSetupStatus.CONFIGURED
                else -> ZebraDataWedgeSetupStatus.AVAILABLE
            },
            zebraDataWedgeMessage = if (isAvailable) {
                if (state.zebraDataWedgeStatus == ZebraDataWedgeSetupStatus.ERROR) {
                    state.zebraDataWedgeMessage
                } else {
                    null
                }
            } else {
                null
            },
        )
    }

    fun beginZebraDataWedgeProvisioning() {
        if (state.zebraDataWedgeStatus == ZebraDataWedgeSetupStatus.UNAVAILABLE) {
            return
        }
        state = state.copy(
            zebraDataWedgeStatus = ZebraDataWedgeSetupStatus.APPLYING,
            zebraDataWedgeMessage = null,
        )
    }

    fun applyZebraDataWedgeResult(result: ZebraDataWedgeResult) {
        state = when (result) {
            ZebraDataWedgeResult.Configured -> state.copy(
                zebraDataWedgeStatus = ZebraDataWedgeSetupStatus.CONFIGURED,
                zebraDataWedgeMessage = null,
            )

            is ZebraDataWedgeResult.Error -> state.copy(
                zebraDataWedgeStatus = ZebraDataWedgeSetupStatus.ERROR,
                zebraDataWedgeMessage = result.message,
            )
        }
    }

    private fun lookupNormalizedBarcode(rawBarcode: String, source: ScanLookupSource) {
        val normalizedBarcode = scanner.normalizeDetectedValue(rawBarcode)
        if (normalizedBarcode == null) {
            state = state.copy(
                productId = null,
                barcode = "",
                productName = "",
                skuCode = "",
                priceLabel = "",
                stockLabel = "",
                stockOnHand = null,
                reorderPoint = null,
                targetStock = null,
                availabilityStatus = "",
                errorMessage = "Scan a valid barcode to continue.",
                lastScanSource = source,
            )
            return
        }

        lookupResolvedBarcode(normalizedBarcode, source)
    }

    private fun lookupResolvedBarcode(normalizedBarcode: String, source: ScanLookupSource) {
        val record = try {
            repository.lookupBarcode(normalizedBarcode)
        } catch (error: IllegalArgumentException) {
            state = state.copy(
                draftBarcode = normalizedBarcode,
                productId = null,
                barcode = normalizedBarcode,
                productName = "",
                skuCode = "",
                priceLabel = "",
                stockLabel = "",
                stockOnHand = null,
                reorderPoint = null,
                targetStock = null,
                availabilityStatus = "",
                lastScanSource = source,
                errorMessage = error.message ?: "Control-plane request failed.",
            )
            return
        }
        if (record == null) {
            state = state.copy(
                draftBarcode = normalizedBarcode,
                productId = null,
                barcode = normalizedBarcode,
                productName = "",
                skuCode = "",
                priceLabel = "",
                stockLabel = "",
                stockOnHand = null,
                reorderPoint = null,
                targetStock = null,
                availabilityStatus = "",
                lastScanSource = source,
                errorMessage = "No catalog match found for this barcode.",
            )
            return
        }

        state = state.copy(
            draftBarcode = normalizedBarcode,
            productId = record.productId,
            barcode = record.barcode,
            productName = record.productName,
            skuCode = record.skuCode,
            priceLabel = "Rs. %.2f".format(record.sellingPrice),
            stockLabel = record.stockOnHand.toInt().toString(),
            stockOnHand = record.stockOnHand,
            reorderPoint = record.reorderPoint,
            targetStock = record.targetStock,
            availabilityStatus = record.availabilityStatus,
            lastScanSource = source,
            errorMessage = null,
        )
    }

    companion object {
        private const val EXTERNAL_SCANNER_RECENT_WINDOW_MS = 5 * 60 * 1000L
    }
}
