package com.store.mobile.ui.tablet

import com.store.mobile.operations.ExpiryBoard
import com.store.mobile.operations.ExpiryReport
import com.store.mobile.operations.ExpiryRecord
import com.store.mobile.operations.ReceivingBoard
import com.store.mobile.operations.ReceivingBoardRecord
import com.store.mobile.ui.operations.ExpiryUiState
import com.store.mobile.ui.operations.ReceivingUiState
import com.store.mobile.ui.operations.RestockUiState
import com.store.mobile.ui.operations.StockCountUiState
import com.store.mobile.ui.runtime.buildRuntimeStatusState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class InventoryTabletOverviewModelTest {
    @Test
    fun prioritizesRuntimeRecoveryWhenTabletIsDisconnected() {
        val model = buildInventoryTabletOverviewModel(
            receivingState = ReceivingUiState(),
            stockCountState = StockCountUiState(),
            restockState = RestockUiState(),
            expiryState = ExpiryUiState(),
            runtimeStatusState = buildRuntimeStatusState(
                connected = false,
                pendingSyncCount = 3,
            ),
        )

        assertEquals(InventoryTabletDestination.RUNTIME, model.primaryDestination)
        assertEquals("Reconnect runtime", model.primaryActionLabel)
        assertTrue(model.runtimeBanner.contains("Disconnected"))
    }

    @Test
    fun prioritizesReceivingWhenApprovedReceiptsAreWaiting() {
        val model = buildInventoryTabletOverviewModel(
            receivingState = ReceivingUiState(
                receivingBoard = ReceivingBoard(
                    branchId = "branch-1",
                    readyCount = 2,
                    receivedCount = 0,
                    receivedWithVarianceCount = 0,
                    records = listOf(
                        ReceivingBoardRecord(
                            purchaseOrderId = "po-1",
                            purchaseOrderNumber = "PO-001",
                            supplierName = "Acme Wholesale",
                            receivingStatus = "READY",
                            canReceive = true,
                        ),
                    ),
                ),
            ),
            stockCountState = StockCountUiState(),
            restockState = RestockUiState(lowStockCount = 4),
            expiryState = ExpiryUiState(
                report = ExpiryReport(
                    branchId = "branch-1",
                    trackedLotCount = 3,
                    expiringSoonCount = 1,
                    expiredCount = 0,
                    records = listOf(
                        ExpiryRecord(
                            batchLotId = "lot-1",
                            productName = "Acme Tea",
                            batchNumber = "LOT-1",
                            expiryDate = "2026-05-12",
                            remainingQuantity = 4.0,
                            status = "EXPIRING_SOON",
                        ),
                    ),
                ),
                board = ExpiryBoard(
                    branchId = "branch-1",
                    openCount = 0,
                    reviewedCount = 0,
                    approvedCount = 0,
                    canceledCount = 0,
                    records = emptyList(),
                ),
            ),
            runtimeStatusState = buildRuntimeStatusState(
                connected = true,
                pendingSyncCount = 0,
            ),
        )

        assertEquals(InventoryTabletDestination.RECEIVING, model.primaryDestination)
        assertEquals("Review inbound receipts", model.primaryActionLabel)
        assertEquals("2 purchase orders ready", model.receivingSummary)
        assertEquals("4 shelf tasks suggested", model.restockSummary)
    }
}
