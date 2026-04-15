package com.store.mobile.scan

import com.store.mobile.ui.scan.ScanCameraStatus
import com.store.mobile.ui.scan.ScanExternalScannerStatus
import com.store.mobile.ui.scan.ScanLookupSource
import com.store.mobile.ui.scan.ScanLookupViewModel
import com.store.mobile.ui.scan.ZebraDataWedgeSetupStatus
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

        viewModel.updateDraftBarcode(" 1234567890123 ")
        viewModel.lookupDraftBarcode()

        assertEquals("ACME TEA", viewModel.state.productName)
        assertEquals("1234567890123", viewModel.state.barcode)
        assertEquals("18", viewModel.state.stockLabel)
        assertEquals("1234567890123", viewModel.state.draftBarcode)
        assertEquals(ScanLookupSource.MANUAL, viewModel.state.lastScanSource)
    }

    @Test
    fun cameraDetectionResolvesLookupStateAndMarksCameraAsReady() {
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

        viewModel.setCameraPermission(granted = true)
        viewModel.onCameraBarcodeDetected("1234567890123", detectedAtMillis = 5_000L)

        assertEquals(ScanCameraStatus.READY, viewModel.state.cameraStatus)
        assertEquals("1234567890123", viewModel.state.draftBarcode)
        assertEquals("ACME TEA", viewModel.state.productName)
        assertEquals(ScanLookupSource.CAMERA, viewModel.state.lastScanSource)
    }

    @Test
    fun externalScannerDetectionResolvesLookupState() {
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

        viewModel.onExternalScannerDetected(" 1234 5678 90123 ", detectedAtMillis = 7_500L)

        assertEquals("1234567890123", viewModel.state.draftBarcode)
        assertEquals("ACME TEA", viewModel.state.productName)
        assertEquals(ScanLookupSource.EXTERNAL_SCANNER, viewModel.state.lastScanSource)
        assertEquals(ScanExternalScannerStatus.RECENT_SCAN, viewModel.state.externalScannerStatus)
        assertEquals("1970-01-01T00:00:07.500Z", viewModel.state.lastExternalScanAt)
    }

    @Test
    fun malformedExternalScannerPayloadMovesStateToPayloadError() {
        val viewModel = ScanLookupViewModel(InMemoryScanLookupRepository())

        viewModel.reportExternalScannerPayloadError("Missing barcode payload.")

        assertEquals(ScanExternalScannerStatus.PAYLOAD_ERROR, viewModel.state.externalScannerStatus)
        assertEquals("Missing barcode payload.", viewModel.state.externalScannerMessage)
    }

    @Test
    fun recognizedScannerCanReturnToReadyAfterRecentWindowExpires() {
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

        viewModel.onExternalScannerDetected("1234567890123", detectedAtMillis = 7_500L)
        viewModel.refreshExternalScannerStatus(referenceTimeMillis = 7_500L + 301_000L)

        assertEquals(ScanExternalScannerStatus.READY, viewModel.state.externalScannerStatus)
    }

    @Test
    fun deniedCameraPermissionMovesStateToPermissionRequired() {
        val viewModel = ScanLookupViewModel(InMemoryScanLookupRepository())

        viewModel.setCameraPermission(granted = false)

        assertEquals(ScanCameraStatus.PERMISSION_REQUIRED, viewModel.state.cameraStatus)
    }

    @Test
    fun cameraFailureMovesStateToUnavailable() {
        val viewModel = ScanLookupViewModel(InMemoryScanLookupRepository())

        viewModel.reportCameraUnavailable("Camera binding failed.")

        assertEquals(ScanCameraStatus.UNAVAILABLE, viewModel.state.cameraStatus)
        assertEquals("Camera binding failed.", viewModel.state.cameraMessage)
    }

    @Test
    fun zebraAvailabilityAndProvisioningSuccessMoveThroughExpectedStates() {
        val viewModel = ScanLookupViewModel(InMemoryScanLookupRepository())

        viewModel.updateZebraDataWedgeAvailability(isAvailable = true)
        viewModel.beginZebraDataWedgeProvisioning()
        viewModel.applyZebraDataWedgeResult(ZebraDataWedgeResult.Configured)

        assertEquals(ZebraDataWedgeSetupStatus.CONFIGURED, viewModel.state.zebraDataWedgeStatus)
        assertEquals(null, viewModel.state.zebraDataWedgeMessage)
    }

    @Test
    fun zebraProvisioningFailureMovesStateToError() {
        val viewModel = ScanLookupViewModel(InMemoryScanLookupRepository())

        viewModel.updateZebraDataWedgeAvailability(isAvailable = true)
        viewModel.beginZebraDataWedgeProvisioning()
        viewModel.applyZebraDataWedgeResult(
            ZebraDataWedgeResult.Error(
                message = "DataWedge rejected the profile bundle.",
                resultCode = "PLUGIN_BUNDLE_INVALID",
            ),
        )

        assertEquals(ZebraDataWedgeSetupStatus.ERROR, viewModel.state.zebraDataWedgeStatus)
        assertEquals("DataWedge rejected the profile bundle.", viewModel.state.zebraDataWedgeMessage)
    }
}
