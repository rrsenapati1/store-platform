package com.store.mobile.ui.handheld

import com.store.mobile.operations.ReceivingDraft
import com.store.mobile.operations.ReceivingDraftLine
import com.store.mobile.operations.StockCountReviewSession
import com.store.mobile.ui.operations.ExpiryUiState
import com.store.mobile.ui.operations.ReceivingUiState
import com.store.mobile.ui.operations.RestockTaskUiRecord
import com.store.mobile.ui.operations.RestockUiState
import com.store.mobile.ui.operations.StockCountUiState
import com.store.mobile.ui.scan.ScanCameraStatus
import com.store.mobile.ui.scan.ScanLookupUiState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class HandheldRuntimePostureModelTest {
    @Test
    fun idleScanPostureHighlightsReadiness() {
        val model = buildHandheldScanHeroModel(
            state = ScanLookupUiState(
                cameraStatus = ScanCameraStatus.CHECKING,
            ),
            actionModel = HandheldScanActionModel(
                primaryAction = HandheldScanAction(
                    label = "Scan another",
                    section = com.store.mobile.ui.operations.MobileOperationsSection.SCAN,
                ),
            ),
        )

        assertEquals("Scan ready", model.eyebrow)
        assertEquals("Scanner warming up", model.title)
        assertTrue(model.detail.contains("Preparing"))
        assertEquals("Scan another", model.primaryActionLabel)
    }

    @Test
    fun scanErrorsProduceRecoveryPosture() {
        val model = buildHandheldScanHeroModel(
            state = ScanLookupUiState(
                errorMessage = "No catalog match found for this barcode.",
                draftBarcode = "12345",
            ),
            actionModel = HandheldScanActionModel(
                primaryAction = HandheldScanAction(
                    label = "Count item",
                    section = com.store.mobile.ui.operations.MobileOperationsSection.STOCK_COUNT,
                ),
            ),
        )

        assertEquals("Needs attention", model.eyebrow)
        assertEquals("Lookup needs attention", model.title)
        assertTrue(model.detail.contains("No catalog match found"))
        assertEquals("Count item", model.primaryActionLabel)
    }

    @Test
    fun emptyTaskStateExplainsHowToResumeWork() {
        val model = buildHandheldTaskPostureModel(
            receivingState = ReceivingUiState(),
            stockCountState = StockCountUiState(),
            restockState = RestockUiState(),
            expiryState = ExpiryUiState(),
        )

        assertEquals("Task queues clear", model.eyebrow)
        assertEquals("No active task queues", model.title)
        assertTrue(model.detail.contains("Use Scan"))
    }

    @Test
    fun activeTaskStateSummarizesResumableWork() {
        val model = buildHandheldTaskPostureModel(
            receivingState = ReceivingUiState(
                activeDraft = ReceivingDraft(
                    purchaseOrderId = "po-1",
                    purchaseOrderNumber = "PO-001",
                    supplierName = "Acme Wholesale",
                    lines = listOf(
                        ReceivingDraftLine(
                            productId = "prod-1",
                            productName = "ACME TEA",
                            skuCode = "TEA-001",
                            orderedQuantity = 24.0,
                        ),
                    ),
                ),
            ),
            stockCountState = StockCountUiState(
                activeSession = StockCountReviewSession(
                    id = "session-1",
                    sessionNumber = "SCNT-001",
                    productId = "prod-1",
                    productName = "ACME TEA",
                    skuCode = "TEA-001",
                    status = "OPEN",
                ),
            ),
            restockState = RestockUiState(
                activeTask = RestockTaskUiRecord(
                    taskId = "task-1",
                    taskNumber = "RST-001",
                    productId = "prod-1",
                    productName = "ACME TEA",
                    skuCode = "TEA-001",
                    status = "OPEN",
                    requestedQuantity = 5,
                    sourcePosture = "BACKROOM_AVAILABLE",
                    activeTaskId = "task-1",
                ),
            ),
            expiryState = ExpiryUiState(),
        )

        assertEquals("Resume work", model.eyebrow)
        assertEquals("3 active tasks underway", model.title)
        assertTrue(model.detail.contains("Receiving"))
        assertTrue(model.detail.contains("Count"))
        assertTrue(model.detail.contains("Restock"))
    }
}
