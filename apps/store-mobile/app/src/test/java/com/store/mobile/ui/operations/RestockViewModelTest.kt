package com.store.mobile.ui.operations

import com.store.mobile.operations.InMemoryRestockRepository
import com.store.mobile.ui.scan.ScanLookupUiState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class RestockViewModelTest {
    @Test
    fun syncsScannedProductAndRunsRestockLifecycle() {
        val viewModel = RestockViewModel(repository = InMemoryRestockRepository())

        viewModel.loadBranch(branchId = "branch-demo-1")
        viewModel.syncScannedLookup(
            ScanLookupUiState(
                productId = "prod-demo-1",
                productName = "ACME TEA",
                skuCode = "TEA-001",
                barcode = "1234567890123",
                stockLabel = "18",
                stockOnHand = 18.0,
                reorderPoint = 10.0,
                targetStock = 24.0,
            ),
        )
        viewModel.updateRequestedQuantity("12")
        viewModel.updatePickedQuantity("10")
        viewModel.updateNote("Counter shelf gap")
        viewModel.createRestockTaskForCurrentProduct()

        assertEquals("ACME TEA", viewModel.state.productName)
        assertEquals(6, viewModel.state.suggestedQuantity)
        assertEquals(1, viewModel.state.openCount)
        assertEquals("RST-BRANCHDEMO1-0001", viewModel.state.activeTask?.taskNumber)

        viewModel.pickActiveTaskForCurrentProduct()
        assertEquals(1, viewModel.state.pickedCount)
        assertEquals("PICKED", viewModel.state.activeTask?.status)

        viewModel.updateCompletionNote("Shelf filled before rush hour")
        viewModel.completeActiveTaskForCurrentProduct()

        assertEquals(1, viewModel.state.completedCount)
        assertNull(viewModel.state.activeTask)
        assertEquals("COMPLETED", viewModel.state.records.first().status)
    }
}
