package com.store.mobile.operations

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ReceivingRepositoryTest {
    @Test
    fun loadsReceivingBoardForBranch() {
        val repository = InMemoryReceivingRepository()

        val board = repository.loadReceivingBoard(branchId = "branch-1")

        assertEquals("PO-001", board.records.first().purchaseOrderNumber)
    }

    @Test
    fun createsReviewedPartialReceiptAndMarksBoardAsReceivedWithVariance() {
        val repository = InMemoryReceivingRepository()
        val draft = repository.loadReceivingDraft(branchId = "branch-demo-1")

        val goodsReceipt = repository.createReviewedReceipt(
            branchId = "branch-demo-1",
            input = CreateReviewedReceiptInput(
                purchaseOrderId = draft.purchaseOrderId,
                note = "Second product held back pending supplier replacement",
                lines = listOf(
                    ReviewedReceiptLineInput(
                        productId = draft.lines[0].productId,
                        receivedQuantity = 20.0,
                        discrepancyNote = "Four cartons short",
                    ),
                    ReviewedReceiptLineInput(
                        productId = draft.lines[1].productId,
                        receivedQuantity = 0.0,
                        discrepancyNote = "Supplier held dispatch",
                    ),
                ),
            ),
        )

        assertEquals("GRN-BRANCHDEMO1-0001", goodsReceipt.goodsReceiptNumber)
        assertTrue(goodsReceipt.hasDiscrepancy)
        assertEquals(20.0, goodsReceipt.receivedQuantityTotal, 0.001)
        assertEquals(14.0, goodsReceipt.varianceQuantityTotal, 0.001)

        val board = repository.loadReceivingBoard(branchId = "branch-demo-1")
        assertEquals(1, board.receivedCount)
        assertEquals(1, board.receivedWithVarianceCount)
        assertEquals("RECEIVED_WITH_VARIANCE", board.records.first().receivingStatus)
        assertEquals(14.0, board.records.first().varianceQuantity, 0.001)
        assertEquals(false, board.records.first().canReceive)
    }
}
