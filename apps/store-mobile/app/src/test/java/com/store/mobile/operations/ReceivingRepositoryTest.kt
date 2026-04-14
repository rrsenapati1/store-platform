package com.store.mobile.operations

import org.junit.Assert.assertEquals
import org.junit.Test

class ReceivingRepositoryTest {
    @Test
    fun loadsReceivingBoardForBranch() {
        val repository = InMemoryReceivingRepository()

        val board = repository.loadReceivingBoard(branchId = "branch-1")

        assertEquals("PO-001", board.records.first().purchaseOrderNumber)
    }
}
