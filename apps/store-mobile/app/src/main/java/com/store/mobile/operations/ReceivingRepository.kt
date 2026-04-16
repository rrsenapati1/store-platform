package com.store.mobile.operations

import kotlin.math.max

data class ReceivingBoardRecord(
    val purchaseOrderId: String,
    val purchaseOrderNumber: String,
    val supplierName: String,
    val receivingStatus: String,
    val canReceive: Boolean,
    val hasDiscrepancy: Boolean = false,
    val varianceQuantity: Double = 0.0,
)

data class ReceivingBoard(
    val branchId: String,
    val readyCount: Int,
    val receivedCount: Int,
    val receivedWithVarianceCount: Int,
    val records: List<ReceivingBoardRecord>,
)

data class ReceivingDraftLine(
    val productId: String,
    val productName: String,
    val skuCode: String,
    val orderedQuantity: Double,
)

data class ReceivingDraft(
    val purchaseOrderId: String,
    val purchaseOrderNumber: String,
    val supplierName: String,
    val lines: List<ReceivingDraftLine>,
)

data class ReviewedReceiptLineInput(
    val productId: String,
    val receivedQuantity: Double,
    val discrepancyNote: String? = null,
)

data class CreateReviewedReceiptInput(
    val purchaseOrderId: String,
    val note: String? = null,
    val lines: List<ReviewedReceiptLineInput>,
)

data class ReviewedGoodsReceiptLine(
    val productId: String,
    val productName: String,
    val skuCode: String,
    val orderedQuantity: Double,
    val quantity: Double,
    val varianceQuantity: Double,
    val discrepancyNote: String? = null,
)

data class ReviewedGoodsReceipt(
    val goodsReceiptId: String,
    val goodsReceiptNumber: String,
    val purchaseOrderId: String,
    val receivedOn: String,
    val note: String? = null,
    val receivedQuantityTotal: Double,
    val varianceQuantityTotal: Double,
    val hasDiscrepancy: Boolean,
    val lines: List<ReviewedGoodsReceiptLine>,
)

interface ReceivingRepository {
    fun loadReceivingBoard(branchId: String): ReceivingBoard
    fun loadReceivingDraft(branchId: String): ReceivingDraft?
    fun latestGoodsReceipt(branchId: String): ReviewedGoodsReceipt?
    fun createReviewedReceipt(branchId: String, input: CreateReviewedReceiptInput): ReviewedGoodsReceipt
}

class InMemoryReceivingRepository : ReceivingRepository {
    private val stateByBranch = mutableMapOf<String, BranchReceivingState>()

    override fun loadReceivingBoard(branchId: String): ReceivingBoard {
        val state = branchState(branchId)
        val latestReceipt = state.latestGoodsReceipt
        val receivingStatus = when {
            latestReceipt == null -> "READY"
            latestReceipt.hasDiscrepancy -> "RECEIVED_WITH_VARIANCE"
            else -> "RECEIVED"
        }
        val canReceive = latestReceipt == null
        val varianceQuantity = latestReceipt?.varianceQuantityTotal ?: 0.0
        val hasDiscrepancy = latestReceipt?.hasDiscrepancy == true
        val record = ReceivingBoardRecord(
            purchaseOrderId = state.draft.purchaseOrderId,
            purchaseOrderNumber = state.draft.purchaseOrderNumber,
            supplierName = state.draft.supplierName,
            receivingStatus = receivingStatus,
            canReceive = canReceive,
            hasDiscrepancy = hasDiscrepancy,
            varianceQuantity = varianceQuantity,
        )
        return ReceivingBoard(
            branchId = branchId,
            readyCount = if (receivingStatus == "READY") 1 else 0,
            receivedCount = if (receivingStatus != "READY") 1 else 0,
            receivedWithVarianceCount = if (receivingStatus == "RECEIVED_WITH_VARIANCE") 1 else 0,
            records = listOf(record),
        )
    }

    override fun loadReceivingDraft(branchId: String): ReceivingDraft {
        return branchState(branchId).draft
    }

    override fun latestGoodsReceipt(branchId: String): ReviewedGoodsReceipt? {
        return branchState(branchId).latestGoodsReceipt
    }

    override fun createReviewedReceipt(branchId: String, input: CreateReviewedReceiptInput): ReviewedGoodsReceipt {
        val state = branchState(branchId)
        require(state.latestGoodsReceipt == null) { "Goods receipt already exists for purchase order." }
        require(input.purchaseOrderId == state.draft.purchaseOrderId) { "Unknown purchase order for branch receiving draft." }
        require(input.lines.size == state.draft.lines.size) { "Every purchase-order line must be reviewed exactly once." }

        val lineByProductId = state.draft.lines.associateBy { it.productId }
        val reviewedLines = input.lines.map { lineInput ->
            val draftLine = requireNotNull(lineByProductId[lineInput.productId]) {
                "Unknown reviewed receipt product."
            }
            require(lineInput.receivedQuantity >= 0) { "Received quantity must be zero or greater." }
            require(lineInput.receivedQuantity <= draftLine.orderedQuantity) { "Received quantity cannot exceed ordered quantity." }
            val varianceQuantity = max(draftLine.orderedQuantity - lineInput.receivedQuantity, 0.0)
            ReviewedGoodsReceiptLine(
                productId = draftLine.productId,
                productName = draftLine.productName,
                skuCode = draftLine.skuCode,
                orderedQuantity = draftLine.orderedQuantity,
                quantity = lineInput.receivedQuantity,
                varianceQuantity = varianceQuantity,
                discrepancyNote = lineInput.discrepancyNote?.takeIf { it.isNotBlank() },
            )
        }
        require(reviewedLines.sumOf { it.quantity } > 0) { "At least one reviewed receiving line must have positive quantity." }

        val receipt = ReviewedGoodsReceipt(
            goodsReceiptId = "goods-receipt-1",
            goodsReceiptNumber = "GRN-${branchId.uppercase().filter(Char::isLetterOrDigit)}-0001",
            purchaseOrderId = input.purchaseOrderId,
            receivedOn = "2026-04-16",
            note = input.note?.takeIf { it.isNotBlank() },
            receivedQuantityTotal = reviewedLines.sumOf { it.quantity },
            varianceQuantityTotal = reviewedLines.sumOf { it.varianceQuantity },
            hasDiscrepancy = reviewedLines.any { it.varianceQuantity > 0 || !it.discrepancyNote.isNullOrBlank() },
            lines = reviewedLines,
        )
        stateByBranch[branchId] = state.copy(latestGoodsReceipt = receipt)
        return receipt
    }

    private fun branchState(branchId: String): BranchReceivingState {
        return stateByBranch.getOrPut(branchId) {
            BranchReceivingState(
                draft = ReceivingDraft(
                    purchaseOrderId = "po-1",
                    purchaseOrderNumber = "PO-001",
                    supplierName = "Acme Wholesale",
                    lines = listOf(
                        ReceivingDraftLine(
                            productId = "prod-demo-1",
                            productName = "ACME TEA",
                            skuCode = "TEA-001",
                            orderedQuantity = 24.0,
                        ),
                        ReceivingDraftLine(
                            productId = "prod-demo-2",
                            productName = "GINGER TEA",
                            skuCode = "TEA-002",
                            orderedQuantity = 10.0,
                        ),
                    ),
                ),
            )
        }
    }

    private data class BranchReceivingState(
        val draft: ReceivingDraft,
        val latestGoodsReceipt: ReviewedGoodsReceipt? = null,
    )
}
