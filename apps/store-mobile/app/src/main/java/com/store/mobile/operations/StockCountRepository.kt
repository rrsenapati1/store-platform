package com.store.mobile.operations

data class StockCountRecord(
    val productId: String,
    val productName: String,
    val skuCode: String,
    val expectedQuantity: Double,
)

data class StockCountContext(
    val branchId: String,
    val records: List<StockCountRecord>,
)

data class StockCountReviewSession(
    val id: String,
    val sessionNumber: String,
    val productId: String,
    val productName: String,
    val skuCode: String,
    val status: String,
    val expectedQuantity: Double? = null,
    val countedQuantity: Double? = null,
    val varianceQuantity: Double? = null,
    val note: String? = null,
    val reviewNote: String? = null,
)

data class ApprovedStockCount(
    val id: String,
    val sessionId: String,
    val productId: String,
    val countedQuantity: Double,
    val expectedQuantity: Double,
    val varianceQuantity: Double,
    val closingStock: Double,
    val note: String? = null,
)

data class StockCountApproval(
    val session: StockCountReviewSession,
    val stockCount: ApprovedStockCount,
)

data class StockCountBoard(
    val branchId: String,
    val openCount: Int,
    val countedCount: Int,
    val approvedCount: Int,
    val canceledCount: Int,
    val records: List<StockCountReviewSession>,
)

interface StockCountRepository {
    fun loadStockCountContext(branchId: String): StockCountContext
    fun loadStockCountBoard(branchId: String): StockCountBoard
    fun latestApprovedCount(branchId: String): StockCountApproval?
    fun createStockCountSession(branchId: String, productId: String, note: String? = null): StockCountReviewSession
    fun recordBlindCount(branchId: String, sessionId: String, countedQuantity: Double, note: String? = null): StockCountReviewSession
    fun approveCountSession(branchId: String, sessionId: String, reviewNote: String? = null): StockCountApproval
    fun cancelCountSession(branchId: String, sessionId: String, reviewNote: String? = null): StockCountReviewSession
}

class InMemoryStockCountRepository : StockCountRepository {
    private val statesByBranch = mutableMapOf<String, BranchStockCountState>()

    override fun loadStockCountContext(branchId: String): StockCountContext {
        return branchState(branchId).context
    }

    override fun loadStockCountBoard(branchId: String): StockCountBoard {
        val sessions = branchState(branchId).sessions.sortedByDescending { it.sessionNumber }
        return StockCountBoard(
            branchId = branchId,
            openCount = sessions.count { it.status == STATUS_OPEN },
            countedCount = sessions.count { it.status == STATUS_COUNTED },
            approvedCount = sessions.count { it.status == STATUS_APPROVED },
            canceledCount = sessions.count { it.status == STATUS_CANCELED },
            records = sessions,
        )
    }

    override fun latestApprovedCount(branchId: String): StockCountApproval? {
        return branchState(branchId).latestApproval
    }

    override fun createStockCountSession(branchId: String, productId: String, note: String?): StockCountReviewSession {
        val state = branchState(branchId)
        val record = requireNotNull(state.context.records.firstOrNull { it.productId == productId }) {
            "Unknown stock-count product for branch."
        }
        require(
            state.sessions.none { it.productId == productId && (it.status == STATUS_OPEN || it.status == STATUS_COUNTED) },
        ) { "Active stock-count session already exists for product." }
        val sequence = state.sessions.size + 1
        val session = StockCountReviewSession(
            id = "stock-count-session-$sequence",
            sessionNumber = "SCNT-${branchId.uppercase().filter(Char::isLetterOrDigit)}-${sequence.toString().padStart(4, '0')}",
            productId = record.productId,
            productName = record.productName,
            skuCode = record.skuCode,
            status = STATUS_OPEN,
            note = note?.takeIf { it.isNotBlank() },
        )
        statesByBranch[branchId] = state.copy(sessions = state.sessions + session)
        return session
    }

    override fun recordBlindCount(
        branchId: String,
        sessionId: String,
        countedQuantity: Double,
        note: String?,
    ): StockCountReviewSession {
        require(countedQuantity >= 0) { "Blind count quantity must be zero or greater." }
        return updateSession(branchId, sessionId) { session, state ->
            require(session.status == STATUS_OPEN) { "Blind count can only be recorded for open sessions." }
            val expectedQuantity = requireNotNull(
                state.context.records.firstOrNull { it.productId == session.productId }?.expectedQuantity,
            )
            session.copy(
                status = STATUS_COUNTED,
                expectedQuantity = expectedQuantity,
                countedQuantity = countedQuantity,
                varianceQuantity = countedQuantity - expectedQuantity,
                note = note?.takeIf { it.isNotBlank() } ?: session.note,
            )
        }
    }

    override fun approveCountSession(
        branchId: String,
        sessionId: String,
        reviewNote: String?,
    ): StockCountApproval {
        val state = branchState(branchId)
        val session = requireNotNull(state.sessions.firstOrNull { it.id == sessionId }) { "Stock-count session not found." }
        require(session.status == STATUS_COUNTED) { "Only counted stock-count sessions can be approved." }
        val approvedSession = session.copy(
            status = STATUS_APPROVED,
            reviewNote = reviewNote?.takeIf { it.isNotBlank() },
        )
        val stockCount = ApprovedStockCount(
            id = "approved-stock-count-${state.approvalSequence + 1}",
            sessionId = approvedSession.id,
            productId = approvedSession.productId,
            countedQuantity = requireNotNull(approvedSession.countedQuantity),
            expectedQuantity = requireNotNull(approvedSession.expectedQuantity),
            varianceQuantity = requireNotNull(approvedSession.varianceQuantity),
            closingStock = requireNotNull(approvedSession.countedQuantity),
            note = approvedSession.reviewNote ?: approvedSession.note,
        )
        val updatedSessions = state.sessions.map { existing ->
            if (existing.id == sessionId) approvedSession else existing
        }
        statesByBranch[branchId] = state.copy(
            sessions = updatedSessions,
            latestApproval = StockCountApproval(session = approvedSession, stockCount = stockCount),
            approvalSequence = state.approvalSequence + 1,
        )
        return requireNotNull(statesByBranch[branchId]?.latestApproval)
    }

    override fun cancelCountSession(branchId: String, sessionId: String, reviewNote: String?): StockCountReviewSession {
        return updateSession(branchId, sessionId) { session, _ ->
            require(session.status == STATUS_OPEN || session.status == STATUS_COUNTED) {
                "Approved stock-count sessions cannot be canceled."
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
        transform: (StockCountReviewSession, BranchStockCountState) -> StockCountReviewSession,
    ): StockCountReviewSession {
        val state = branchState(branchId)
        val index = state.sessions.indexOfFirst { it.id == sessionId }
        require(index >= 0) { "Stock-count session not found." }
        val updatedSession = transform(state.sessions[index], state)
        val updatedSessions = state.sessions.toMutableList().also { it[index] = updatedSession }
        statesByBranch[branchId] = state.copy(sessions = updatedSessions)
        return updatedSession
    }

    private fun branchState(branchId: String): BranchStockCountState {
        return statesByBranch.getOrPut(branchId) {
            BranchStockCountState(
                context = StockCountContext(
                    branchId = branchId,
                    records = listOf(
                        StockCountRecord(
                            productId = "prod-demo-1",
                            productName = "ACME TEA",
                            skuCode = "TEA-001",
                            expectedQuantity = 18.0,
                        ),
                    ),
                ),
            )
        }
    }

    private data class BranchStockCountState(
        val context: StockCountContext,
        val sessions: List<StockCountReviewSession> = emptyList(),
        val latestApproval: StockCountApproval? = null,
        val approvalSequence: Int = 0,
    )

    companion object {
        private const val STATUS_OPEN = "OPEN"
        private const val STATUS_COUNTED = "COUNTED"
        private const val STATUS_APPROVED = "APPROVED"
        private const val STATUS_CANCELED = "CANCELED"
    }
}
