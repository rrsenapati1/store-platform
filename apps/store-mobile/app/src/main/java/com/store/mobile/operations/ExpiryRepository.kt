package com.store.mobile.operations

data class ExpiryRecord(
    val batchLotId: String,
    val productName: String,
    val batchNumber: String,
    val expiryDate: String,
    val remainingQuantity: Double,
    val status: String,
)

data class ExpiryReport(
    val branchId: String,
    val trackedLotCount: Int,
    val expiringSoonCount: Int,
    val expiredCount: Int,
    val records: List<ExpiryRecord>,
)

data class ExpiryReviewSession(
    val id: String,
    val sessionNumber: String,
    val batchLotId: String,
    val productName: String,
    val batchNumber: String,
    val expiryDate: String,
    val status: String,
    val remainingQuantitySnapshot: Double,
    val proposedQuantity: Double? = null,
    val reason: String? = null,
    val note: String? = null,
    val reviewNote: String? = null,
)

data class ApprovedExpiryWriteOff(
    val id: String,
    val sessionId: String,
    val batchLotId: String,
    val batchNumber: String,
    val productName: String,
    val writeOffQuantity: Double,
    val remainingQuantityAfterWriteOff: Double,
    val statusAfterWriteOff: String,
    val reason: String,
    val note: String? = null,
)

data class ExpiryReviewApproval(
    val session: ExpiryReviewSession,
    val writeOff: ApprovedExpiryWriteOff,
)

data class ExpiryBoard(
    val branchId: String,
    val openCount: Int,
    val reviewedCount: Int,
    val approvedCount: Int,
    val canceledCount: Int,
    val records: List<ExpiryReviewSession>,
)

interface ExpiryRepository {
    fun loadExpiryReport(branchId: String): ExpiryReport
    fun loadExpiryBoard(branchId: String): ExpiryBoard
    fun latestApprovedWriteOff(branchId: String): ExpiryReviewApproval?
    fun createExpirySession(branchId: String, batchLotId: String, note: String? = null): ExpiryReviewSession
    fun recordExpiryReview(
        branchId: String,
        sessionId: String,
        proposedQuantity: Double,
        reason: String,
        note: String? = null,
    ): ExpiryReviewSession
    fun approveExpirySession(branchId: String, sessionId: String, reviewNote: String? = null): ExpiryReviewApproval
    fun cancelExpirySession(branchId: String, sessionId: String, reviewNote: String? = null): ExpiryReviewSession
}

class InMemoryExpiryRepository : ExpiryRepository {
    private val statesByBranch = mutableMapOf<String, BranchExpiryState>()

    override fun loadExpiryReport(branchId: String): ExpiryReport {
        val records = branchState(branchId).reportRecords
        return buildExpiryReport(branchId, records)
    }

    override fun loadExpiryBoard(branchId: String): ExpiryBoard {
        val sessions = branchState(branchId).sessions.sortedByDescending { it.sessionNumber }
        return ExpiryBoard(
            branchId = branchId,
            openCount = sessions.count { it.status == STATUS_OPEN },
            reviewedCount = sessions.count { it.status == STATUS_REVIEWED },
            approvedCount = sessions.count { it.status == STATUS_APPROVED },
            canceledCount = sessions.count { it.status == STATUS_CANCELED },
            records = sessions,
        )
    }

    override fun latestApprovedWriteOff(branchId: String): ExpiryReviewApproval? {
        return branchState(branchId).latestApproval
    }

    override fun createExpirySession(branchId: String, batchLotId: String, note: String?): ExpiryReviewSession {
        val state = branchState(branchId)
        val record = requireNotNull(state.reportRecords.firstOrNull { it.batchLotId == batchLotId }) {
            "Unknown expiry batch lot for branch."
        }
        require(
            state.sessions.none { it.batchLotId == batchLotId && (it.status == STATUS_OPEN || it.status == STATUS_REVIEWED) },
        ) { "Active expiry session already exists for batch lot." }
        val sequence = state.sessions.size + 1
        val session = ExpiryReviewSession(
            id = "expiry-session-$sequence",
            sessionNumber = "EXP-${branchId.uppercase().filter(Char::isLetterOrDigit)}-${sequence.toString().padStart(4, '0')}",
            batchLotId = record.batchLotId,
            productName = record.productName,
            batchNumber = record.batchNumber,
            expiryDate = record.expiryDate,
            status = STATUS_OPEN,
            remainingQuantitySnapshot = record.remainingQuantity,
            note = note?.takeIf { it.isNotBlank() },
        )
        statesByBranch[branchId] = state.copy(sessions = state.sessions + session)
        return session
    }

    override fun recordExpiryReview(
        branchId: String,
        sessionId: String,
        proposedQuantity: Double,
        reason: String,
        note: String?,
    ): ExpiryReviewSession {
        require(proposedQuantity > 0) { "Expiry write-off quantity must be greater than zero." }
        require(reason.isNotBlank()) { "Expiry review reason is required." }
        return updateSession(branchId, sessionId) { session, state ->
            require(session.status == STATUS_OPEN) { "Expiry review can only be recorded for open sessions." }
            val currentRemaining = requireNotNull(
                state.reportRecords.firstOrNull { it.batchLotId == session.batchLotId }?.remainingQuantity,
            )
            require(proposedQuantity <= currentRemaining) {
                "Expiry write-off quantity cannot exceed remaining stock."
            }
            session.copy(
                status = STATUS_REVIEWED,
                proposedQuantity = proposedQuantity,
                reason = reason,
                note = note?.takeIf { it.isNotBlank() } ?: session.note,
            )
        }
    }

    override fun approveExpirySession(branchId: String, sessionId: String, reviewNote: String?): ExpiryReviewApproval {
        val state = branchState(branchId)
        val session = requireNotNull(state.sessions.firstOrNull { it.id == sessionId }) { "Expiry session not found." }
        require(session.status == STATUS_REVIEWED) { "Only reviewed expiry sessions can be approved." }
        val currentRecord = requireNotNull(state.reportRecords.firstOrNull { it.batchLotId == session.batchLotId }) {
            "Expiry batch lot not found."
        }
        val proposedQuantity = requireNotNull(session.proposedQuantity)
        require(proposedQuantity <= currentRecord.remainingQuantity) {
            "Expiry write-off quantity cannot exceed remaining stock."
        }
        val updatedRecord = currentRecord.copy(
            remainingQuantity = currentRecord.remainingQuantity - proposedQuantity,
            status = if (currentRecord.remainingQuantity - proposedQuantity <= 0) STATUS_EXPIRED else currentRecord.status,
        )
        val approvedSession = session.copy(
            status = STATUS_APPROVED,
            reviewNote = reviewNote?.takeIf { it.isNotBlank() },
        )
        val writeOff = ApprovedExpiryWriteOff(
            id = "approved-expiry-write-off-${state.approvalSequence + 1}",
            sessionId = approvedSession.id,
            batchLotId = approvedSession.batchLotId,
            batchNumber = approvedSession.batchNumber,
            productName = approvedSession.productName,
            writeOffQuantity = proposedQuantity,
            remainingQuantityAfterWriteOff = updatedRecord.remainingQuantity,
            statusAfterWriteOff = updatedRecord.status,
            reason = requireNotNull(approvedSession.reason),
            note = approvedSession.reviewNote ?: approvedSession.note,
        )
        val updatedSessions = state.sessions.map { existing ->
            if (existing.id == sessionId) approvedSession else existing
        }
        val updatedRecords = state.reportRecords.map { existing ->
            if (existing.batchLotId == currentRecord.batchLotId) updatedRecord else existing
        }
        statesByBranch[branchId] = state.copy(
            reportRecords = updatedRecords,
            sessions = updatedSessions,
            latestApproval = ExpiryReviewApproval(session = approvedSession, writeOff = writeOff),
            approvalSequence = state.approvalSequence + 1,
        )
        return requireNotNull(statesByBranch[branchId]?.latestApproval)
    }

    override fun cancelExpirySession(branchId: String, sessionId: String, reviewNote: String?): ExpiryReviewSession {
        return updateSession(branchId, sessionId) { session, _ ->
            require(session.status == STATUS_OPEN || session.status == STATUS_REVIEWED) {
                "Approved expiry sessions cannot be canceled."
            }
            session.copy(
                status = STATUS_CANCELED,
                reviewNote = reviewNote?.takeIf { it.isNotBlank() },
            )
        }
    }

    private fun updateSession(
        branchId: String,
        sessionId: String,
        transform: (ExpiryReviewSession, BranchExpiryState) -> ExpiryReviewSession,
    ): ExpiryReviewSession {
        val state = branchState(branchId)
        val index = state.sessions.indexOfFirst { it.id == sessionId }
        require(index >= 0) { "Expiry session not found." }
        val updatedSession = transform(state.sessions[index], state)
        val updatedSessions = state.sessions.toMutableList().also { it[index] = updatedSession }
        statesByBranch[branchId] = state.copy(sessions = updatedSessions)
        return updatedSession
    }

    private fun branchState(branchId: String): BranchExpiryState {
        return statesByBranch.getOrPut(branchId) {
            BranchExpiryState(
                reportRecords = listOf(
                    ExpiryRecord(
                        batchLotId = "batch-1",
                        productName = "ACME TEA",
                        batchNumber = "BATCH-EXP-1",
                        expiryDate = "2026-05-20",
                        remainingQuantity = 6.0,
                        status = STATUS_EXPIRING_SOON,
                    ),
                ),
            )
        }
    }

    private fun buildExpiryReport(branchId: String, records: List<ExpiryRecord>): ExpiryReport {
        return ExpiryReport(
            branchId = branchId,
            trackedLotCount = records.size,
            expiringSoonCount = records.count { it.status == STATUS_EXPIRING_SOON },
            expiredCount = records.count { it.status == STATUS_EXPIRED },
            records = records,
        )
    }

    private data class BranchExpiryState(
        val reportRecords: List<ExpiryRecord>,
        val sessions: List<ExpiryReviewSession> = emptyList(),
        val latestApproval: ExpiryReviewApproval? = null,
        val approvalSequence: Int = 0,
    )

    companion object {
        private const val STATUS_OPEN = "OPEN"
        private const val STATUS_REVIEWED = "REVIEWED"
        private const val STATUS_APPROVED = "APPROVED"
        private const val STATUS_CANCELED = "CANCELED"
        private const val STATUS_EXPIRING_SOON = "EXPIRING_SOON"
        private const val STATUS_EXPIRED = "EXPIRED"
    }
}
