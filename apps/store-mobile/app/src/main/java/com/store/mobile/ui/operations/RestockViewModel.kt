package com.store.mobile.ui.operations

import com.store.mobile.operations.CreateRestockTaskInput
import com.store.mobile.operations.RestockBoard
import com.store.mobile.operations.RestockBoardRecord
import com.store.mobile.operations.RestockRepository
import com.store.mobile.ui.scan.ScanLookupUiState
import kotlin.math.max

data class RestockTaskUiRecord(
    val taskId: String,
    val taskNumber: String,
    val productId: String,
    val productName: String,
    val skuCode: String,
    val status: String,
    val requestedQuantity: Int,
    val pickedQuantity: Int? = null,
    val sourcePosture: String,
    val note: String? = null,
    val completionNote: String? = null,
    val activeTaskId: String? = null,
)

data class RestockUiState(
    val productId: String? = null,
    val productName: String = "",
    val skuCode: String = "",
    val stockOnHand: Int? = null,
    val reorderPoint: Int? = null,
    val targetStock: Int? = null,
    val suggestedQuantity: Int? = null,
    val requestedQuantity: String = "",
    val pickedQuantity: String = "",
    val note: String = "",
    val completionNote: String = "",
    val sourcePosture: String = "BACKROOM_AVAILABLE",
    val openCount: Int = 0,
    val pickedCount: Int = 0,
    val completedCount: Int = 0,
    val canceledCount: Int = 0,
    val records: List<RestockTaskUiRecord> = emptyList(),
    val activeTask: RestockTaskUiRecord? = null,
    val errorMessage: String? = null,
)

class RestockViewModel(
    private val repository: RestockRepository,
) {
    private var branchId: String? = null

    var state: RestockUiState = RestockUiState()
        private set

    fun loadBranch(branchId: String) {
        this.branchId = branchId
        refreshBoard()
    }

    fun clearBranch() {
        branchId = null
        state = RestockUiState()
    }

    fun syncScannedLookup(scanState: ScanLookupUiState) {
        val productId = scanState.productId?.takeIf { it.isNotBlank() }
        val stockOnHand = scanState.stockOnHand?.toInt()
        val reorderPoint = scanState.reorderPoint?.toInt()
        val targetStock = scanState.targetStock?.toInt()
        val suggestedQuantity = if (stockOnHand != null && targetStock != null) {
            max(targetStock - stockOnHand, 0)
        } else {
            null
        }
        state = state.copy(
            productId = productId,
            productName = scanState.productName,
            skuCode = scanState.skuCode,
            stockOnHand = stockOnHand,
            reorderPoint = reorderPoint,
            targetStock = targetStock,
            suggestedQuantity = suggestedQuantity,
            activeTask = deriveActiveTask(state.records, productId),
        )
    }

    fun updateRequestedQuantity(value: String) {
        state = state.copy(requestedQuantity = value)
    }

    fun updatePickedQuantity(value: String) {
        state = state.copy(pickedQuantity = value)
    }

    fun updateNote(value: String) {
        state = state.copy(note = value)
    }

    fun updateCompletionNote(value: String) {
        state = state.copy(completionNote = value)
    }

    fun updateSourcePosture(value: String) {
        state = state.copy(sourcePosture = value)
    }

    fun refreshBoard() {
        val currentBranchId = branchId ?: return
        applyBoard(repository.loadRestockBoard(currentBranchId))
    }

    fun createRestockTaskForCurrentProduct() {
        val currentBranchId = branchId ?: return
        val productId = state.productId ?: run {
            state = state.copy(errorMessage = "Scan and look up a product first.")
            return
        }
        val requestedQuantity = state.requestedQuantity.toDoubleOrNull()
        if (requestedQuantity == null || requestedQuantity <= 0) {
            state = state.copy(errorMessage = "Requested quantity must be greater than zero.")
            return
        }
        val stockOnHand = state.stockOnHand?.toDouble()
        val reorderPoint = state.reorderPoint?.toDouble()
        val targetStock = state.targetStock?.toDouble()
        if (stockOnHand == null || reorderPoint == null || targetStock == null) {
            state = state.copy(errorMessage = "This product does not have a branch replenishment policy yet.")
            return
        }

        try {
            repository.createRestockTask(
                branchId = currentBranchId,
                input = CreateRestockTaskInput(
                    productId = productId,
                    productName = state.productName,
                    skuCode = state.skuCode,
                    stockOnHandSnapshot = stockOnHand,
                    reorderPointSnapshot = reorderPoint,
                    targetStockSnapshot = targetStock,
                    requestedQuantity = requestedQuantity,
                    sourcePosture = state.sourcePosture,
                    note = state.note,
                ),
            )
            applyBoard(repository.loadRestockBoard(currentBranchId))
        } catch (error: IllegalArgumentException) {
            state = state.copy(errorMessage = error.message ?: "Unable to create restock task.")
        }
    }

    fun pickActiveTaskForCurrentProduct() {
        val currentBranchId = branchId ?: return
        val activeTask = state.activeTask ?: run {
            state = state.copy(errorMessage = "No active restock task for the current product.")
            return
        }
        val pickedQuantity = state.pickedQuantity.toDoubleOrNull()
        if (pickedQuantity == null || pickedQuantity < 0) {
            state = state.copy(errorMessage = "Picked quantity must be zero or greater.")
            return
        }

        try {
            repository.pickRestockTask(
                branchId = currentBranchId,
                taskId = activeTask.taskId,
                pickedQuantity = pickedQuantity,
                note = state.note,
            )
            applyBoard(repository.loadRestockBoard(currentBranchId))
        } catch (error: IllegalArgumentException) {
            state = state.copy(errorMessage = error.message ?: "Unable to mark restock task picked.")
        }
    }

    fun completeActiveTaskForCurrentProduct() {
        val currentBranchId = branchId ?: return
        val activeTask = state.activeTask ?: run {
            state = state.copy(errorMessage = "No active restock task for the current product.")
            return
        }

        try {
            repository.completeRestockTask(
                branchId = currentBranchId,
                taskId = activeTask.taskId,
                completionNote = state.completionNote,
            )
            applyBoard(repository.loadRestockBoard(currentBranchId))
        } catch (error: IllegalArgumentException) {
            state = state.copy(errorMessage = error.message ?: "Unable to complete restock task.")
        }
    }

    fun cancelActiveTaskForCurrentProduct() {
        val currentBranchId = branchId ?: return
        val activeTask = state.activeTask ?: run {
            state = state.copy(errorMessage = "No active restock task for the current product.")
            return
        }

        try {
            repository.cancelRestockTask(
                branchId = currentBranchId,
                taskId = activeTask.taskId,
                cancelNote = state.completionNote.ifBlank { state.note },
            )
            applyBoard(repository.loadRestockBoard(currentBranchId))
        } catch (error: IllegalArgumentException) {
            state = state.copy(errorMessage = error.message ?: "Unable to cancel restock task.")
        }
    }

    private fun applyBoard(board: RestockBoard) {
        val records = board.records.map(::toUiRecord)
        state = state.copy(
            openCount = board.openCount,
            pickedCount = board.pickedCount,
            completedCount = board.completedCount,
            canceledCount = board.canceledCount,
            records = records,
            activeTask = deriveActiveTask(records, state.productId),
            errorMessage = null,
        )
    }

    private fun deriveActiveTask(
        records: List<RestockTaskUiRecord>,
        currentProductId: String?,
    ): RestockTaskUiRecord? {
        if (currentProductId == null) {
            return null
        }
        return records.firstOrNull { it.productId == currentProductId && it.activeTaskId != null }
    }

    private fun toUiRecord(record: RestockBoardRecord): RestockTaskUiRecord {
        return RestockTaskUiRecord(
            taskId = record.taskId,
            taskNumber = record.taskNumber,
            productId = record.productId,
            productName = record.productName,
            skuCode = record.skuCode,
            status = record.status,
            requestedQuantity = record.requestedQuantity.toInt(),
            pickedQuantity = record.pickedQuantity?.toInt(),
            sourcePosture = record.sourcePosture,
            note = record.note,
            completionNote = record.completionNote,
            activeTaskId = record.activeTaskId,
        )
    }

    companion object {
        const val DEFAULT_SOURCE_POSTURE = "BACKROOM_AVAILABLE"
    }
}
