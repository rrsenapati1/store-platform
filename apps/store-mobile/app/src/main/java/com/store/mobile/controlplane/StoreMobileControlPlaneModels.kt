package com.store.mobile.controlplane

data class ControlPlaneInventorySnapshotRecord(
    val productId: String,
    val productName: String,
    val skuCode: String,
    val stockOnHand: Double,
    val lastEntryType: String,
)

data class ControlPlaneInventorySnapshotResponse(
    val records: List<ControlPlaneInventorySnapshotRecord>,
)

data class ControlPlaneCatalogScanRecord(
    val productId: String,
    val productName: String,
    val skuCode: String,
    val barcode: String,
    val sellingPrice: Double,
    val stockOnHand: Double,
    val availabilityStatus: String,
    val reorderPoint: Double? = null,
    val targetStock: Double? = null,
)

data class ControlPlaneReceivingBoardRecord(
    val purchaseOrderId: String,
    val purchaseOrderNumber: String,
    val supplierName: String,
    val approvalStatus: String,
    val receivingStatus: String,
    val canReceive: Boolean,
    val hasDiscrepancy: Boolean = false,
    val varianceQuantity: Double = 0.0,
    val blockedReason: String? = null,
    val goodsReceiptId: String? = null,
)

data class ControlPlaneReceivingBoard(
    val branchId: String,
    val blockedCount: Int,
    val readyCount: Int,
    val receivedCount: Int,
    val receivedWithVarianceCount: Int,
    val records: List<ControlPlaneReceivingBoardRecord>,
)

data class ControlPlanePurchaseOrderLine(
    val productId: String,
    val productName: String,
    val skuCode: String,
    val quantity: Double,
    val unitCost: Double,
    val lineTotal: Double,
)

data class ControlPlanePurchaseOrder(
    val id: String,
    val tenantId: String,
    val branchId: String,
    val supplierId: String,
    val purchaseOrderNumber: String,
    val approvalStatus: String,
    val subtotal: Double,
    val taxTotal: Double,
    val grandTotal: Double,
    val lines: List<ControlPlanePurchaseOrderLine>,
)

data class ControlPlaneGoodsReceiptLineReceiveInput(
    val productId: String,
    val receivedQuantity: Double,
    val discrepancyNote: String? = null,
)

data class ControlPlaneGoodsReceiptLine(
    val productId: String,
    val productName: String,
    val skuCode: String,
    val orderedQuantity: Double,
    val quantity: Double,
    val varianceQuantity: Double,
    val unitCost: Double,
    val lineTotal: Double,
    val discrepancyNote: String? = null,
)

data class ControlPlaneGoodsReceipt(
    val id: String,
    val tenantId: String,
    val branchId: String,
    val purchaseOrderId: String,
    val supplierId: String,
    val goodsReceiptNumber: String,
    val receivedOn: String,
    val note: String? = null,
    val orderedQuantityTotal: Double,
    val receivedQuantityTotal: Double,
    val varianceQuantityTotal: Double,
    val hasDiscrepancy: Boolean,
    val lines: List<ControlPlaneGoodsReceiptLine>,
)

data class ControlPlaneGoodsReceiptRecord(
    val goodsReceiptId: String,
    val goodsReceiptNumber: String,
    val purchaseOrderId: String,
    val purchaseOrderNumber: String,
    val supplierId: String,
    val supplierName: String,
    val receivedOn: String,
    val lineCount: Int,
    val receivedQuantity: Double,
    val orderedQuantity: Double,
    val varianceQuantity: Double,
    val hasDiscrepancy: Boolean,
    val note: String? = null,
)

data class ControlPlaneGoodsReceiptListResponse(
    val records: List<ControlPlaneGoodsReceiptRecord>,
)

data class ControlPlaneStockCountReviewSession(
    val id: String,
    val tenantId: String,
    val branchId: String,
    val productId: String,
    val sessionNumber: String,
    val status: String,
    val expectedQuantity: Double? = null,
    val countedQuantity: Double? = null,
    val varianceQuantity: Double? = null,
    val note: String? = null,
    val reviewNote: String? = null,
)

data class ControlPlaneStockCount(
    val id: String,
    val tenantId: String,
    val branchId: String,
    val productId: String,
    val countedQuantity: Double,
    val expectedQuantity: Double,
    val varianceQuantity: Double,
    val note: String? = null,
    val closingStock: Double,
)

data class ControlPlaneStockCountApproval(
    val session: ControlPlaneStockCountReviewSession,
    val stockCount: ControlPlaneStockCount,
)

data class ControlPlaneStockCountBoardRecord(
    val stockCountSessionId: String,
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

data class ControlPlaneStockCountBoard(
    val branchId: String,
    val openCount: Int,
    val countedCount: Int,
    val approvedCount: Int,
    val canceledCount: Int,
    val records: List<ControlPlaneStockCountBoardRecord>,
)

data class ControlPlaneBatchExpiryReportRecord(
    val batchLotId: String,
    val productId: String,
    val productName: String,
    val batchNumber: String,
    val expiryDate: String,
    val daysToExpiry: Int,
    val receivedQuantity: Double,
    val writtenOffQuantity: Double,
    val remainingQuantity: Double,
    val status: String,
)

data class ControlPlaneBatchExpiryReport(
    val branchId: String,
    val trackedLotCount: Int,
    val expiringSoonCount: Int,
    val expiredCount: Int,
    val untrackedStockQuantity: Double,
    val records: List<ControlPlaneBatchExpiryReportRecord>,
)

data class ControlPlaneBatchExpiryReviewSession(
    val id: String,
    val tenantId: String,
    val branchId: String,
    val batchLotId: String,
    val productId: String,
    val sessionNumber: String,
    val status: String,
    val remainingQuantitySnapshot: Double,
    val proposedQuantity: Double? = null,
    val reason: String? = null,
    val note: String? = null,
    val reviewNote: String? = null,
)

data class ControlPlaneBatchExpiryWriteOff(
    val batchLotId: String,
    val productId: String,
    val productName: String,
    val batchNumber: String,
    val expiryDate: String,
    val receivedQuantity: Double,
    val writtenOffQuantity: Double,
    val remainingQuantity: Double,
    val status: String,
    val reason: String,
)

data class ControlPlaneBatchExpiryApproval(
    val session: ControlPlaneBatchExpiryReviewSession,
    val writeOff: ControlPlaneBatchExpiryWriteOff,
)

data class ControlPlaneBatchExpiryBoardRecord(
    val batchExpirySessionId: String,
    val sessionNumber: String,
    val batchLotId: String,
    val productId: String,
    val productName: String,
    val skuCode: String,
    val batchNumber: String,
    val status: String,
    val remainingQuantitySnapshot: Double,
    val proposedQuantity: Double? = null,
    val reason: String? = null,
    val note: String? = null,
    val reviewNote: String? = null,
)

data class ControlPlaneBatchExpiryBoard(
    val branchId: String,
    val openCount: Int,
    val reviewedCount: Int,
    val approvedCount: Int,
    val canceledCount: Int,
    val records: List<ControlPlaneBatchExpiryBoardRecord>,
)

data class ControlPlaneRestockTask(
    val id: String,
    val tenantId: String,
    val branchId: String,
    val productId: String,
    val taskNumber: String,
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

data class ControlPlaneRestockBoardRecord(
    val restockTaskId: String,
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
    val hasActiveTask: Boolean,
)

data class ControlPlaneRestockBoard(
    val branchId: String,
    val openCount: Int,
    val pickedCount: Int,
    val completedCount: Int,
    val canceledCount: Int,
    val records: List<ControlPlaneRestockBoardRecord>,
)
