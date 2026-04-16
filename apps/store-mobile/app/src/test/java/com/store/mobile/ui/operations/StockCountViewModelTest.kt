package com.store.mobile.ui.operations

import com.store.mobile.operations.InMemoryStockCountRepository
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Test

class StockCountViewModelTest {
    @Test
    fun runsReviewedStockCountLifecycle() {
        val viewModel = StockCountViewModel(repository = InMemoryStockCountRepository())

        viewModel.loadBranch(branchId = "branch-demo-1")
        viewModel.createSessionForProduct(productId = "prod-demo-1", note = "Blind count before aisle reset")

        assertEquals(1, viewModel.state.board?.openCount)
        assertEquals("SCNT-BRANCHDEMO1-0001", viewModel.state.activeSession?.sessionNumber)

        viewModel.updateBlindCountQuantity("16")
        viewModel.updateBlindCountNote("Two boxes missing from front shelf")
        viewModel.recordBlindCountForActiveSession()

        assertEquals("COUNTED", viewModel.state.activeSession?.status)
        assertEquals(-2, viewModel.state.activeSession?.varianceQuantity?.toInt())

        viewModel.updateReviewNote("Variance accepted after aisle check")
        viewModel.approveActiveSession()

        assertEquals(1, viewModel.state.board?.approvedCount)
        assertEquals("APPROVED", viewModel.state.latestApprovedCount?.session?.status)
        assertNotNull(viewModel.state.latestApprovedCount?.stockCount)
    }
}
