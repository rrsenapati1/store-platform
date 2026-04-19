package com.store.mobile.ui.handheld

import com.store.mobile.operations.ReceivingDraft
import com.store.mobile.operations.ReceivingDraftLine
import com.store.mobile.operations.StockCountReviewSession
import com.store.mobile.ui.operations.ExpiryUiState
import com.store.mobile.ui.operations.MobileOperationsSection
import com.store.mobile.ui.operations.ReceivingLineDraftUi
import com.store.mobile.ui.operations.ReceivingUiState
import com.store.mobile.ui.operations.RestockTaskUiRecord
import com.store.mobile.ui.operations.RestockUiState
import com.store.mobile.ui.operations.StockCountUiState
import com.store.mobile.ui.scan.ScanLookupUiState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class HandheldScanActionModelTest {
    @Test
    fun scannedItemWithTaskPostureYieldsPrioritizedActions() {
        val model = buildHandheldScanActionModel(
            scanState = ScanLookupUiState(
                productId = "prod-1",
                productName = "ACME TEA",
                skuCode = "TEA-001",
                stockOnHand = 2.0,
                reorderPoint = 5.0,
                targetStock = 12.0,
                availabilityStatus = "LOW_STOCK",
            ),
            receivingState = ReceivingUiState(
                lineDrafts = listOf(
                    ReceivingLineDraftUi(
                        productId = "prod-1",
                        productName = "ACME TEA",
                        skuCode = "TEA-001",
                        orderedQuantity = 24,
                        receivedQuantity = "0",
                        discrepancyNote = "",
                    ),
                ),
            ),
            stockCountState = StockCountUiState(),
            restockState = RestockUiState(lowStockCount = 3),
            expiryState = ExpiryUiState(),
        )

        assertEquals("Receive stock", model.primaryAction.label)
        assertEquals(MobileOperationsSection.RECEIVING, model.primaryAction.section)
        assertTrue(model.secondaryActions.any { it.label == "Restock shelf" && it.section == MobileOperationsSection.RESTOCK })
        assertTrue(model.queuePreview.any { it.label == "Low stock" && it.count == 3 })
    }

    @Test
    fun idlePostureWithoutScannedItemOnlyPromotesScanAgain() {
        val model = buildHandheldScanActionModel(
            scanState = ScanLookupUiState(),
            receivingState = ReceivingUiState(),
            stockCountState = StockCountUiState(),
            restockState = RestockUiState(),
            expiryState = ExpiryUiState(),
        )

        assertEquals("Scan another", model.primaryAction.label)
        assertEquals(MobileOperationsSection.SCAN, model.primaryAction.section)
        assertTrue(model.secondaryActions.isEmpty())
        assertTrue(model.recentTaskContexts.isEmpty())
    }

    @Test
    fun activeOperationalWorkSurfacesResumableTaskContext() {
        val model = buildHandheldScanActionModel(
            scanState = ScanLookupUiState(
                productId = "prod-1",
                productName = "ACME TEA",
                skuCode = "TEA-001",
            ),
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
                    id = "stock-count-session-1",
                    sessionNumber = "SCNT-BRANCH-0001",
                    productId = "prod-1",
                    productName = "ACME TEA",
                    skuCode = "TEA-001",
                    status = "OPEN",
                ),
            ),
            restockState = RestockUiState(
                activeTask = RestockTaskUiRecord(
                    taskId = "restock-task-1",
                    taskNumber = "RST-BRANCH-0001",
                    productId = "prod-1",
                    productName = "ACME TEA",
                    skuCode = "TEA-001",
                    status = "OPEN",
                    requestedQuantity = 6,
                    sourcePosture = "BACKROOM_AVAILABLE",
                    activeTaskId = "restock-task-1",
                ),
            ),
            expiryState = ExpiryUiState(
                activeSession = com.store.mobile.operations.ExpiryReviewSession(
                    id = "expiry-session-1",
                    sessionNumber = "EXP-BRANCH-0001",
                    batchLotId = "batch-1",
                    productName = "ACME TEA",
                    batchNumber = "BATCH-EXP-1",
                    expiryDate = "2026-05-20",
                    status = "OPEN",
                    remainingQuantitySnapshot = 6.0,
                ),
            ),
        )

        assertTrue(model.recentTaskContexts.any { it.title == "Receiving in progress" && it.section == MobileOperationsSection.RECEIVING })
        assertTrue(model.recentTaskContexts.any { it.title == "Count in progress" && it.section == MobileOperationsSection.STOCK_COUNT })
        assertTrue(model.recentTaskContexts.any { it.title == "Restock in progress" && it.section == MobileOperationsSection.RESTOCK })
        assertTrue(model.recentTaskContexts.any { it.title == "Expiry review in progress" && it.section == MobileOperationsSection.EXPIRY })
    }
}
