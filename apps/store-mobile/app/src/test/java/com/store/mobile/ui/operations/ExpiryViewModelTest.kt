package com.store.mobile.ui.operations

import com.store.mobile.operations.InMemoryExpiryRepository
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Test

class ExpiryViewModelTest {
    @Test
    fun runsReviewedExpiryLifecycle() {
        val viewModel = ExpiryViewModel(repository = InMemoryExpiryRepository())

        viewModel.loadBranch(branchId = "branch-demo-1")
        viewModel.createSessionForBatch(batchLotId = "batch-1", note = "Shelf review before write-off")

        assertEquals(1, viewModel.state.board?.openCount)
        assertEquals("EXP-BRANCHDEMO1-0001", viewModel.state.activeSession?.sessionNumber)

        viewModel.updateProposedQuantity("1")
        viewModel.updateWriteOffReason("Expired front pouch")
        viewModel.updateSessionNote("Front shelf damage confirmed")
        viewModel.recordReviewForActiveSession()

        assertEquals("REVIEWED", viewModel.state.activeSession?.status)
        assertEquals(1, viewModel.state.activeSession?.proposedQuantity?.toInt())

        viewModel.updateReviewNote("Approved after shelf review")
        viewModel.approveActiveSession()

        assertEquals(1, viewModel.state.board?.approvedCount)
        assertEquals("APPROVED", viewModel.state.latestApprovedWriteOff?.session?.status)
        assertNotNull(viewModel.state.latestApprovedWriteOff?.writeOff)
    }
}
