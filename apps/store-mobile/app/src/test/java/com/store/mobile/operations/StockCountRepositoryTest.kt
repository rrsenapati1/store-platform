package com.store.mobile.operations

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

class StockCountRepositoryTest {
    @Test
    fun loadsStockCountContextForBranch() {
        val repository = InMemoryStockCountRepository()

        val context = repository.loadStockCountContext(branchId = "branch-1")

        assertEquals("ACME TEA", context.records.first().productName)
    }

    @Test
    fun createsRecordsAndApprovesReviewedStockCountSession() {
        val repository = InMemoryStockCountRepository()

        val session = repository.createStockCountSession(
            branchId = "branch-demo-1",
            productId = "prod-demo-1",
            note = "Blind count before aisle reset",
        )
        assertEquals("OPEN", session.status)
        assertEquals("SCNT-BRANCHDEMO1-0001", session.sessionNumber)
        assertNull(session.countedQuantity)

        val countedSession = repository.recordBlindCount(
            branchId = "branch-demo-1",
            sessionId = session.id,
            countedQuantity = 16.0,
            note = "Two boxes missing from front shelf",
        )
        assertEquals("COUNTED", countedSession.status)
        assertNotNull(countedSession.expectedQuantity)
        assertNotNull(countedSession.varianceQuantity)
        assertEquals(18.0, requireNotNull(countedSession.expectedQuantity), 0.001)
        assertEquals(-2.0, requireNotNull(countedSession.varianceQuantity), 0.001)

        val approval = repository.approveCountSession(
            branchId = "branch-demo-1",
            sessionId = session.id,
            reviewNote = "Variance accepted after aisle check",
        )
        assertEquals("APPROVED", approval.session.status)
        assertEquals(-2.0, approval.stockCount.varianceQuantity, 0.001)
        assertEquals(16.0, approval.stockCount.closingStock, 0.001)

        val board = repository.loadStockCountBoard(branchId = "branch-demo-1")
        assertEquals(0, board.openCount)
        assertEquals(0, board.countedCount)
        assertEquals(1, board.approvedCount)
        assertEquals("APPROVED", board.records.first().status)
    }
}
