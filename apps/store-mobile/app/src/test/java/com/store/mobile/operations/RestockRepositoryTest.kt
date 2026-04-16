package com.store.mobile.operations

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class RestockRepositoryTest {
    @Test
    fun createsPicksAndCompletesRestockTaskWithoutLeavingAnActiveTask() {
        val repository = InMemoryRestockRepository()

        val createdTask = repository.createRestockTask(
            branchId = "branch-demo-1",
            input = CreateRestockTaskInput(
                productId = "prod-demo-1",
                productName = "ACME TEA",
                skuCode = "TEA-001",
                stockOnHandSnapshot = 18.0,
                reorderPointSnapshot = 10.0,
                targetStockSnapshot = 24.0,
                requestedQuantity = 12.0,
                sourcePosture = "BACKROOM_AVAILABLE",
                note = "Counter shelf gap",
            ),
        )

        assertEquals("RST-BRANCHDEMO1-0001", createdTask.taskNumber)
        assertEquals("OPEN", createdTask.status)
        assertEquals(6.0, createdTask.suggestedQuantitySnapshot, 0.001)

        repository.pickRestockTask(
            branchId = "branch-demo-1",
            taskId = createdTask.id,
            pickedQuantity = 10.0,
            note = "Picked from backroom rack A",
        )
        repository.completeRestockTask(
            branchId = "branch-demo-1",
            taskId = createdTask.id,
            completionNote = "Shelf filled before rush hour",
        )

        val board = repository.loadRestockBoard(branchId = "branch-demo-1")

        assertEquals(0, board.openCount)
        assertEquals(0, board.pickedCount)
        assertEquals(1, board.completedCount)
        assertEquals(0, board.canceledCount)
        assertEquals("COMPLETED", board.records.first().status)
        assertEquals("Shelf filled before rush hour", board.records.first().completionNote)
        assertNull(board.records.first().activeTaskId)
    }
}
