package com.store.mobile.ui.operations

import com.store.mobile.operations.ExpiryReport
import com.store.mobile.operations.ExpiryRepository
import com.store.mobile.operations.ExpiryReviewApproval
import com.store.mobile.operations.ExpiryReviewSession
import com.store.mobile.operations.ExpiryBoard

data class ExpiryUiState(
    val report: ExpiryReport? = null,
    val board: ExpiryBoard? = null,
    val activeSession: ExpiryReviewSession? = null,
    val latestApprovedWriteOff: ExpiryReviewApproval? = null,
    val proposedQuantity: String = "",
    val writeOffReason: String = "",
    val sessionNote: String = "",
    val reviewNote: String = "",
    val errorMessage: String? = null,
)

class ExpiryViewModel(
    private val repository: ExpiryRepository,
) {
    private var branchId: String? = null

    var state: ExpiryUiState = ExpiryUiState()
        private set

    fun loadBranch(branchId: String) {
        this.branchId = branchId
        val report = repository.loadExpiryReport(branchId)
        val board = repository.loadExpiryBoard(branchId)
        val activeSession = board.records.firstOrNull { it.status == "OPEN" || it.status == "REVIEWED" }
        state = ExpiryUiState(
            report = report,
            board = board,
            activeSession = activeSession,
            latestApprovedWriteOff = repository.latestApprovedWriteOff(branchId),
            proposedQuantity = activeSession?.proposedQuantity?.toInt()?.toString() ?: "",
            writeOffReason = activeSession?.reason.orEmpty(),
            sessionNote = activeSession?.note.orEmpty(),
            reviewNote = activeSession?.reviewNote.orEmpty(),
        )
    }

    fun clearBranch() {
        branchId = null
        state = ExpiryUiState()
    }

    fun createSessionForBatch(batchLotId: String, note: String? = null) {
        val currentBranchId = branchId ?: return
        try {
            repository.createExpirySession(currentBranchId, batchLotId, note)
            refreshFromRepository(currentBranchId)
        } catch (error: IllegalArgumentException) {
            state = state.copy(errorMessage = error.message ?: "Unable to create expiry session.")
        }
    }

    fun updateProposedQuantity(value: String) {
        state = state.copy(proposedQuantity = value)
    }

    fun updateWriteOffReason(value: String) {
        state = state.copy(writeOffReason = value)
    }

    fun updateSessionNote(value: String) {
        state = state.copy(sessionNote = value)
    }

    fun updateReviewNote(value: String) {
        state = state.copy(reviewNote = value)
    }

    fun recordReviewForActiveSession() {
        val currentBranchId = branchId ?: return
        val session = state.activeSession ?: run {
            state = state.copy(errorMessage = "No active expiry session.")
            return
        }
        val proposedQuantity = state.proposedQuantity.toDoubleOrNull()
        if (proposedQuantity == null) {
            state = state.copy(errorMessage = "Write-off quantity must be numeric.")
            return
        }
        try {
            repository.recordExpiryReview(
                branchId = currentBranchId,
                sessionId = session.id,
                proposedQuantity = proposedQuantity,
                reason = state.writeOffReason,
                note = state.sessionNote,
            )
            refreshFromRepository(currentBranchId)
        } catch (error: IllegalArgumentException) {
            state = state.copy(errorMessage = error.message ?: "Unable to record expiry review.")
        }
    }

    fun approveActiveSession() {
        val currentBranchId = branchId ?: return
        val session = state.activeSession ?: run {
            state = state.copy(errorMessage = "No active expiry session.")
            return
        }
        try {
            repository.approveExpirySession(
                branchId = currentBranchId,
                sessionId = session.id,
                reviewNote = state.reviewNote,
            )
            refreshFromRepository(currentBranchId)
        } catch (error: IllegalArgumentException) {
            state = state.copy(errorMessage = error.message ?: "Unable to approve expiry session.")
        }
    }

    fun cancelActiveSession() {
        val currentBranchId = branchId ?: return
        val session = state.activeSession ?: run {
            state = state.copy(errorMessage = "No active expiry session.")
            return
        }
        try {
            repository.cancelExpirySession(
                branchId = currentBranchId,
                sessionId = session.id,
                reviewNote = state.reviewNote.ifBlank { state.sessionNote },
            )
            refreshFromRepository(currentBranchId)
        } catch (error: IllegalArgumentException) {
            state = state.copy(errorMessage = error.message ?: "Unable to cancel expiry session.")
        }
    }

    private fun refreshFromRepository(branchId: String) {
        val report = repository.loadExpiryReport(branchId)
        val board = repository.loadExpiryBoard(branchId)
        val activeSession = board.records.firstOrNull { it.status == "OPEN" || it.status == "REVIEWED" }
        state = state.copy(
            report = report,
            board = board,
            activeSession = activeSession,
            latestApprovedWriteOff = repository.latestApprovedWriteOff(branchId),
            proposedQuantity = activeSession?.proposedQuantity?.toInt()?.toString() ?: "",
            writeOffReason = activeSession?.reason.orEmpty(),
            sessionNote = activeSession?.note.orEmpty(),
            reviewNote = activeSession?.reviewNote.orEmpty(),
            errorMessage = null,
        )
    }
}
