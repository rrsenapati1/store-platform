package com.store.mobile.operations

data class ReceivingBoardRecord(
    val purchaseOrderId: String,
    val purchaseOrderNumber: String,
    val supplierName: String,
    val receivingStatus: String,
    val canReceive: Boolean,
)

data class ReceivingBoard(
    val branchId: String,
    val records: List<ReceivingBoardRecord>,
)

interface ReceivingRepository {
    fun loadReceivingBoard(branchId: String): ReceivingBoard
}

class InMemoryReceivingRepository : ReceivingRepository {
    override fun loadReceivingBoard(branchId: String): ReceivingBoard {
        return ReceivingBoard(
            branchId = branchId,
            records = listOf(
                ReceivingBoardRecord(
                    purchaseOrderId = "po-1",
                    purchaseOrderNumber = "PO-001",
                    supplierName = "Acme Wholesale",
                    receivingStatus = "READY",
                    canReceive = true,
                ),
            ),
        )
    }
}
