package com.store.mobile.operations

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Test

class ExpiryRepositoryTest {
    @Test
    fun loadsExpiryRecordsForBranch() {
        val repository = InMemoryExpiryRepository()

        val report = repository.loadExpiryReport(branchId = "branch-1")

        assertEquals("BATCH-EXP-1", report.records.first().batchNumber)
    }

    @Test
    fun createsReviewsAndApprovesExpirySession() {
        val repository = InMemoryExpiryRepository()

        val session = repository.createExpirySession(
            branchId = "branch-demo-1",
            batchLotId = "batch-1",
            note = "Shelf review before write-off",
        )
        assertEquals("OPEN", session.status)
        assertEquals("EXP-BRANCHDEMO1-0001", session.sessionNumber)

        val reviewedSession = repository.recordExpiryReview(
            branchId = "branch-demo-1",
            sessionId = session.id,
            proposedQuantity = 1.0,
            reason = "Expired front pouch",
            note = "Front shelf damage confirmed",
        )
        assertEquals("REVIEWED", reviewedSession.status)
        assertNotNull(reviewedSession.proposedQuantity)
        assertEquals(1.0, requireNotNull(reviewedSession.proposedQuantity), 0.001)
        assertEquals("Expired front pouch", reviewedSession.reason)

        val approval = repository.approveExpirySession(
            branchId = "branch-demo-1",
            sessionId = session.id,
            reviewNote = "Approved after shelf review",
        )
        assertEquals("APPROVED", approval.session.status)
        assertEquals(1.0, approval.writeOff.writeOffQuantity, 0.001)
        assertEquals(5.0, approval.writeOff.remainingQuantityAfterWriteOff, 0.001)

        val report = repository.loadExpiryReport(branchId = "branch-demo-1")
        assertEquals(5.0, report.records.first().remainingQuantity, 0.001)

        val board = repository.loadExpiryBoard(branchId = "branch-demo-1")
        assertEquals(0, board.openCount)
        assertEquals(0, board.reviewedCount)
        assertEquals(1, board.approvedCount)
        assertEquals("APPROVED", board.records.first().status)
    }
}
