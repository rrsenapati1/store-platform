package com.store.mobile.operations

import kotlin.math.max

data class CreateRestockTaskInput(
    val productId: String,
    val productName: String,
    val skuCode: String,
    val stockOnHandSnapshot: Double,
    val reorderPointSnapshot: Double,
    val targetStockSnapshot: Double,
    val requestedQuantity: Double,
    val sourcePosture: String,
    val note: String? = null,
)

data class RestockTask(
    val id: String,
    val taskNumber: String,
    val productId: String,
    val productName: String,
    val skuCode: String,
    val status: String,
    val stockOnHandSnapshot: Double,
    val reorderPointSnapshot: Double,
    val targetStockSnapshot: Double,
    val suggestedQuantitySnapshot: Double,
    val requestedQuantity: Double,
    val pickedQuantity: Double? = null,
    val sourcePosture: String,
    val note: String? = null,
    val completionNote: String? = null,
)

data class RestockBoardRecord(
    val taskId: String,
    val taskNumber: String,
    val productId: String,
    val productName: String,
    val skuCode: String,
    val status: String,
    val stockOnHandSnapshot: Double,
    val reorderPointSnapshot: Double,
    val targetStockSnapshot: Double,
    val suggestedQuantitySnapshot: Double,
    val requestedQuantity: Double,
    val pickedQuantity: Double? = null,
    val sourcePosture: String,
    val note: String? = null,
    val completionNote: String? = null,
    val activeTaskId: String? = null,
)

data class RestockBoard(
    val branchId: String,
    val openCount: Int,
    val pickedCount: Int,
    val completedCount: Int,
    val canceledCount: Int,
    val records: List<RestockBoardRecord>,
)

data class ReplenishmentBoardRecord(
    val productId: String,
    val productName: String,
    val skuCode: String,
    val stockOnHand: Double,
    val reorderPoint: Double,
    val targetStock: Double,
    val suggestedReorderQuantity: Double,
    val replenishmentStatus: String,
)

data class ReplenishmentBoard(
    val branchId: String,
    val lowStockCount: Int,
    val adequateCount: Int,
    val records: List<ReplenishmentBoardRecord>,
)

interface RestockRepository {
    fun loadRestockBoard(branchId: String): RestockBoard
    fun loadReplenishmentBoard(branchId: String): ReplenishmentBoard
    fun createRestockTask(branchId: String, input: CreateRestockTaskInput): RestockTask
    fun pickRestockTask(branchId: String, taskId: String, pickedQuantity: Double, note: String? = null): RestockTask
    fun completeRestockTask(branchId: String, taskId: String, completionNote: String? = null): RestockTask
    fun cancelRestockTask(branchId: String, taskId: String, cancelNote: String? = null): RestockTask
}

class InMemoryRestockRepository : RestockRepository {
    private val tasksByBranch = mutableMapOf<String, MutableList<RestockTask>>()

    override fun loadRestockBoard(branchId: String): RestockBoard {
        val tasks = tasksByBranch[branchId].orEmpty()
        val sortedTasks = tasks.sortedByDescending { it.taskNumber }
        return RestockBoard(
            branchId = branchId,
            openCount = tasks.count { it.status == STATUS_OPEN },
            pickedCount = tasks.count { it.status == STATUS_PICKED },
            completedCount = tasks.count { it.status == STATUS_COMPLETED },
            canceledCount = tasks.count { it.status == STATUS_CANCELED },
            records = sortedTasks.map { task ->
                RestockBoardRecord(
                    taskId = task.id,
                    taskNumber = task.taskNumber,
                    productId = task.productId,
                    productName = task.productName,
                    skuCode = task.skuCode,
                    status = task.status,
                    stockOnHandSnapshot = task.stockOnHandSnapshot,
                    reorderPointSnapshot = task.reorderPointSnapshot,
                    targetStockSnapshot = task.targetStockSnapshot,
                    suggestedQuantitySnapshot = task.suggestedQuantitySnapshot,
                    requestedQuantity = task.requestedQuantity,
                    pickedQuantity = task.pickedQuantity,
                    sourcePosture = task.sourcePosture,
                    note = task.note,
                    completionNote = task.completionNote,
                    activeTaskId = if (task.status == STATUS_OPEN || task.status == STATUS_PICKED) {
                        task.id
                    } else {
                        null
                    },
                )
            },
        )
    }

    override fun loadReplenishmentBoard(branchId: String): ReplenishmentBoard {
        return ReplenishmentBoard(
            branchId = branchId,
            lowStockCount = 0,
            adequateCount = 0,
            records = emptyList(),
        )
    }

    override fun createRestockTask(branchId: String, input: CreateRestockTaskInput): RestockTask {
        require(input.requestedQuantity > 0) { "Requested quantity must be greater than zero." }
        val existingTasks = tasksByBranch.getOrPut(branchId) { mutableListOf() }
        require(
            existingTasks.none {
                it.productId == input.productId && (it.status == STATUS_OPEN || it.status == STATUS_PICKED)
            },
        ) { "Active restock task already exists for product." }

        val nextSequence = existingTasks.size + 1
        val task = RestockTask(
            id = "restock-task-$nextSequence",
            taskNumber = "RST-${branchId.uppercase().filter(Char::isLetterOrDigit)}-${nextSequence.toString().padStart(4, '0')}",
            productId = input.productId,
            productName = input.productName,
            skuCode = input.skuCode,
            status = STATUS_OPEN,
            stockOnHandSnapshot = input.stockOnHandSnapshot,
            reorderPointSnapshot = input.reorderPointSnapshot,
            targetStockSnapshot = input.targetStockSnapshot,
            suggestedQuantitySnapshot = max(input.targetStockSnapshot - input.stockOnHandSnapshot, 0.0),
            requestedQuantity = input.requestedQuantity,
            sourcePosture = input.sourcePosture,
            note = input.note?.takeIf { it.isNotBlank() },
        )
        existingTasks.add(task)
        return task
    }

    override fun pickRestockTask(branchId: String, taskId: String, pickedQuantity: Double, note: String?): RestockTask {
        require(pickedQuantity >= 0) { "Picked quantity must be zero or greater." }
        return updateTask(branchId, taskId) { task ->
            require(task.status == STATUS_OPEN) { "Only open restock tasks can be picked." }
            require(pickedQuantity <= task.requestedQuantity) { "Picked quantity cannot exceed requested quantity." }
            task.copy(
                status = STATUS_PICKED,
                pickedQuantity = pickedQuantity,
                note = note?.takeIf { it.isNotBlank() } ?: task.note,
            )
        }
    }

    override fun completeRestockTask(branchId: String, taskId: String, completionNote: String?): RestockTask {
        return updateTask(branchId, taskId) { task ->
            require(task.status == STATUS_PICKED) { "Only picked restock tasks can be completed." }
            task.copy(
                status = STATUS_COMPLETED,
                completionNote = completionNote?.takeIf { it.isNotBlank() },
            )
        }
    }

    override fun cancelRestockTask(branchId: String, taskId: String, cancelNote: String?): RestockTask {
        return updateTask(branchId, taskId) { task ->
            require(task.status == STATUS_OPEN || task.status == STATUS_PICKED) { "Completed restock tasks cannot be canceled." }
            task.copy(
                status = STATUS_CANCELED,
                completionNote = cancelNote?.takeIf { it.isNotBlank() },
            )
        }
    }

    private fun updateTask(branchId: String, taskId: String, mutate: (RestockTask) -> RestockTask): RestockTask {
        val tasks = tasksByBranch[branchId] ?: error("Unknown restock branch: $branchId")
        val index = tasks.indexOfFirst { it.id == taskId }
        require(index >= 0) { "Restock task not found." }
        val updatedTask = mutate(tasks[index])
        tasks[index] = updatedTask
        return updatedTask
    }

    companion object {
        private const val STATUS_OPEN = "OPEN"
        private const val STATUS_PICKED = "PICKED"
        private const val STATUS_COMPLETED = "COMPLETED"
        private const val STATUS_CANCELED = "CANCELED"
    }
}
