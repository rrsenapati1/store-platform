package com.store.mobile.ui.operations

import com.store.mobile.operations.StockCountApproval
import com.store.mobile.operations.StockCountBoard
import com.store.mobile.operations.StockCountContext
import com.store.mobile.operations.StockCountRepository
import com.store.mobile.operations.StockCountReviewSession

data class StockCountUiState(
    val context: StockCountContext? = null,
    val board: StockCountBoard? = null,
    val activeSession: StockCountReviewSession? = null,
    val latestApprovedCount: StockCountApproval? = null,
    val blindCountQuantity: String = "",
    val blindCountNote: String = "",
    val reviewNote: String = "",
    val errorMessage: String? = null,
)

class StockCountViewModel(
    private val repository: StockCountRepository,
) {
    private var branchId: String? = null

    var state: StockCountUiState = StockCountUiState()
        private set

    fun loadBranch(branchId: String) {
        this.branchId = branchId
        val context = repository.loadStockCountContext(branchId)
        val board = repository.loadStockCountBoard(branchId)
        val activeSession = board.records.firstOrNull { it.status == "OPEN" || it.status == "COUNTED" }
        state = StockCountUiState(
            context = context,
            board = board,
            activeSession = activeSession,
            latestApprovedCount = repository.latestApprovedCount(branchId),
            blindCountQuantity = activeSession?.countedQuantity?.toInt()?.toString() ?: "",
            blindCountNote = activeSession?.note.orEmpty(),
            reviewNote = activeSession?.reviewNote.orEmpty(),
        )
    }

    fun clearBranch() {
        branchId = null
        state = StockCountUiState()
    }

    fun createSessionForProduct(productId: String, note: String? = null) {
        val currentBranchId = branchId ?: return
        try {
            repository.createStockCountSession(currentBranchId, productId, note)
            refreshFromRepository(currentBranchId)
        } catch (error: IllegalArgumentException) {
            state = state.copy(errorMessage = error.message ?: "Unable to create stock-count session.")
        }
    }

    fun updateBlindCountQuantity(value: String) {
        state = state.copy(blindCountQuantity = value)
    }

    fun updateBlindCountNote(value: String) {
        state = state.copy(blindCountNote = value)
    }

    fun updateReviewNote(value: String) {
        state = state.copy(reviewNote = value)
    }

    fun recordBlindCountForActiveSession() {
        val currentBranchId = branchId ?: return
        val session = state.activeSession ?: run {
            state = state.copy(errorMessage = "No active stock-count session.")
            return
        }
        val blindCountQuantity = state.blindCountQuantity.toDoubleOrNull()
        if (blindCountQuantity == null) {
            state = state.copy(errorMessage = "Blind count quantity must be numeric.")
            return
        }
        try {
            repository.recordBlindCount(
                branchId = currentBranchId,
                sessionId = session.id,
                countedQuantity = blindCountQuantity,
                note = state.blindCountNote,
            )
            refreshFromRepository(currentBranchId)
        } catch (error: IllegalArgumentException) {
            state = state.copy(errorMessage = error.message ?: "Unable to record blind count.")
        }
    }

    fun approveActiveSession() {
        val currentBranchId = branchId ?: return
        val session = state.activeSession ?: run {
            state = state.copy(errorMessage = "No active stock-count session.")
            return
        }
        try {
            repository.approveCountSession(
                branchId = currentBranchId,
                sessionId = session.id,
                reviewNote = state.reviewNote,
            )
            refreshFromRepository(currentBranchId)
        } catch (error: IllegalArgumentException) {
            state = state.copy(errorMessage = error.message ?: "Unable to approve stock-count session.")
        }
    }

    fun cancelActiveSession() {
        val currentBranchId = branchId ?: return
        val session = state.activeSession ?: run {
            state = state.copy(errorMessage = "No active stock-count session.")
            return
        }
        try {
            repository.cancelCountSession(
                branchId = currentBranchId,
                sessionId = session.id,
                reviewNote = state.reviewNote.ifBlank { state.blindCountNote },
            )
            refreshFromRepository(currentBranchId)
        } catch (error: IllegalArgumentException) {
            state = state.copy(errorMessage = error.message ?: "Unable to cancel stock-count session.")
        }
    }

    private fun refreshFromRepository(branchId: String) {
        val board = repository.loadStockCountBoard(branchId)
        val activeSession = board.records.firstOrNull { it.status == "OPEN" || it.status == "COUNTED" }
        state = state.copy(
            board = board,
            activeSession = activeSession,
            latestApprovedCount = repository.latestApprovedCount(branchId),
            blindCountQuantity = activeSession?.countedQuantity?.toInt()?.toString() ?: "",
            blindCountNote = activeSession?.note.orEmpty(),
            reviewNote = activeSession?.reviewNote.orEmpty(),
            errorMessage = null,
        )
    }
}
