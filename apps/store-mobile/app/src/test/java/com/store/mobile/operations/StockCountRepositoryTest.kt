package com.store.mobile.operations

import org.junit.Assert.assertEquals
import org.junit.Test

class StockCountRepositoryTest {
    @Test
    fun loadsStockCountContextForBranch() {
        val repository = InMemoryStockCountRepository()

        val context = repository.loadStockCountContext(branchId = "branch-1")

        assertEquals("ACME TEA", context.records.first().productName)
    }
}
