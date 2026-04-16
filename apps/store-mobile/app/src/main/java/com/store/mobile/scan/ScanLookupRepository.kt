package com.store.mobile.scan

data class ScanLookupRecord(
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

interface ScanLookupRepository {
    fun lookupBarcode(barcode: String): ScanLookupRecord?
}

class InMemoryScanLookupRepository(
    private val records: List<ScanLookupRecord> = listOf(
        ScanLookupRecord(
            productId = "prod-demo-1",
            productName = "ACME TEA",
            skuCode = "TEA-001",
            barcode = "1234567890123",
            sellingPrice = 125.0,
            stockOnHand = 18.0,
            availabilityStatus = "IN_STOCK",
            reorderPoint = 10.0,
            targetStock = 24.0,
        ),
    ),
) : ScanLookupRepository {
    override fun lookupBarcode(barcode: String): ScanLookupRecord? {
        return records.firstOrNull { it.barcode == barcode }
    }
}
