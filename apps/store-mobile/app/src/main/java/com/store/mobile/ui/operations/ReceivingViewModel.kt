package com.store.mobile.ui.operations

import com.store.mobile.operations.CreateReviewedReceiptInput
import com.store.mobile.operations.ReceivingDraft
import com.store.mobile.operations.ReceivingRepository
import com.store.mobile.operations.ReviewedReceiptLineInput
import com.store.mobile.operations.ReviewedGoodsReceipt
import kotlin.math.max

data class ReceivingLineDraftUi(
    val productId: String,
    val productName: String,
    val skuCode: String,
    val orderedQuantity: Int,
    val receivedQuantity: String,
    val discrepancyNote: String,
)

data class ReceivingSummaryUi(
    val orderedQuantity: Int = 0,
    val receivedQuantity: Int = 0,
    val varianceQuantity: Int = 0,
)

data class ReceivingUiState(
    val receivingBoard: com.store.mobile.operations.ReceivingBoard? = null,
    val activeDraft: ReceivingDraft? = null,
    val lineDrafts: List<ReceivingLineDraftUi> = emptyList(),
    val receiptNote: String = "",
    val receiptSummary: ReceivingSummaryUi = ReceivingSummaryUi(),
    val latestGoodsReceipt: ReviewedGoodsReceipt? = null,
    val errorMessage: String? = null,
)

class ReceivingViewModel(
    private val repository: ReceivingRepository,
) {
    private var branchId: String? = null

    var state: ReceivingUiState = ReceivingUiState()
        private set

    fun loadBranch(branchId: String) {
        this.branchId = branchId
        val draft = repository.loadReceivingDraft(branchId)
        state = ReceivingUiState(
            receivingBoard = repository.loadReceivingBoard(branchId),
            activeDraft = draft,
            lineDrafts = draft?.lines?.map { line ->
                ReceivingLineDraftUi(
                    productId = line.productId,
                    productName = line.productName,
                    skuCode = line.skuCode,
                    orderedQuantity = line.orderedQuantity.toInt(),
                    receivedQuantity = line.orderedQuantity.toInt().toString(),
                    discrepancyNote = "",
                )
            }.orEmpty(),
            latestGoodsReceipt = repository.latestGoodsReceipt(branchId),
        ).refreshSummary()
    }

    fun clearBranch() {
        branchId = null
        state = ReceivingUiState()
    }

    fun updateLineReceivedQuantity(productId: String, value: String) {
        state = state.copy(
            lineDrafts = state.lineDrafts.map { line ->
                if (line.productId == productId) line.copy(receivedQuantity = value) else line
            },
        ).refreshSummary()
    }

    fun updateLineDiscrepancyNote(productId: String, value: String) {
        state = state.copy(
            lineDrafts = state.lineDrafts.map { line ->
                if (line.productId == productId) line.copy(discrepancyNote = value) else line
            },
        )
    }

    fun updateReceiptNote(value: String) {
        state = state.copy(receiptNote = value)
    }

    fun submitReviewedReceipt() {
        val currentBranchId = branchId ?: return
        val draft = state.activeDraft ?: run {
            state = state.copy(errorMessage = "No active reviewed receiving draft for this branch.")
            return
        }

        val reviewedLines = state.lineDrafts.map { line ->
            val receivedQuantity = line.receivedQuantity.toDoubleOrNull()
            if (receivedQuantity == null) {
                state = state.copy(errorMessage = "All receiving quantities must be numeric.")
                return
            }
            ReviewedReceiptLineInput(
                productId = line.productId,
                receivedQuantity = receivedQuantity,
                discrepancyNote = line.discrepancyNote,
            )
        }

        try {
            repository.createReviewedReceipt(
                branchId = currentBranchId,
                input = CreateReviewedReceiptInput(
                    purchaseOrderId = draft.purchaseOrderId,
                    note = state.receiptNote,
                    lines = reviewedLines,
                ),
            )
            state = state.copy(
                receivingBoard = repository.loadReceivingBoard(currentBranchId),
                latestGoodsReceipt = repository.latestGoodsReceipt(currentBranchId),
                errorMessage = null,
            ).refreshSummary()
        } catch (error: IllegalArgumentException) {
            state = state.copy(errorMessage = error.message ?: "Unable to create reviewed goods receipt.")
        }
    }

    private fun ReceivingUiState.refreshSummary(): ReceivingUiState {
        val orderedQuantity = lineDrafts.sumOf { it.orderedQuantity }
        val receivedQuantity = lineDrafts.sumOf { line ->
            line.receivedQuantity.toDoubleOrNull()?.toInt() ?: 0
        }
        return copy(
            receiptSummary = ReceivingSummaryUi(
                orderedQuantity = orderedQuantity,
                receivedQuantity = receivedQuantity,
                varianceQuantity = max(orderedQuantity - receivedQuantity, 0),
            ),
        )
    }
}
