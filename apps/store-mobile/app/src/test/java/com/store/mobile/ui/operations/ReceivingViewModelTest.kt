package com.store.mobile.ui.operations

import com.store.mobile.operations.InMemoryReceivingRepository
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ReceivingViewModelTest {
    @Test
    fun createsReviewedReceiptFromEditableLineDrafts() {
        val viewModel = ReceivingViewModel(repository = InMemoryReceivingRepository())

        viewModel.loadBranch(branchId = "branch-demo-1")
        viewModel.updateLineReceivedQuantity(productId = "prod-demo-1", value = "20")
        viewModel.updateLineDiscrepancyNote(productId = "prod-demo-1", value = "Four cartons short")
        viewModel.updateLineReceivedQuantity(productId = "prod-demo-2", value = "0")
        viewModel.updateLineDiscrepancyNote(productId = "prod-demo-2", value = "Supplier held dispatch")
        viewModel.updateReceiptNote("Second product held back pending supplier replacement")
        viewModel.submitReviewedReceipt()

        assertEquals("GRN-BRANCHDEMO1-0001", viewModel.state.latestGoodsReceipt?.goodsReceiptNumber)
        assertTrue(viewModel.state.latestGoodsReceipt?.hasDiscrepancy == true)
        assertEquals(20, viewModel.state.receiptSummary.receivedQuantity)
        assertEquals(14, viewModel.state.receiptSummary.varianceQuantity)
        assertEquals(1, viewModel.state.receivingBoard?.receivedWithVarianceCount)
        assertEquals("RECEIVED_WITH_VARIANCE", viewModel.state.receivingBoard?.records?.first()?.receivingStatus)
    }
}
