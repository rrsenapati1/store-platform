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

interface StockCountRepository {
    fun loadStockCountContext(branchId: String): StockCountContext
}

class InMemoryStockCountRepository : StockCountRepository {
    override fun loadStockCountContext(branchId: String): StockCountContext {
        return StockCountContext(
            branchId = branchId,
            records = listOf(
                StockCountRecord(
                    productId = "prod-demo-1",
                    productName = "ACME TEA",
                    skuCode = "TEA-001",
                    expectedQuantity = 18.0,
                ),
            ),
        )
    }
}
