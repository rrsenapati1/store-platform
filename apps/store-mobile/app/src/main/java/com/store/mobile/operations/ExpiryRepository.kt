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
    val records: List<ExpiryRecord>,
)

interface ExpiryRepository {
    fun loadExpiryReport(branchId: String): ExpiryReport
}

class InMemoryExpiryRepository : ExpiryRepository {
    override fun loadExpiryReport(branchId: String): ExpiryReport {
        return ExpiryReport(
            branchId = branchId,
            records = listOf(
                ExpiryRecord(
                    batchLotId = "batch-1",
                    productName = "ACME TEA",
                    batchNumber = "BATCH-EXP-1",
                    expiryDate = "2026-05-20",
                    remainingQuantity = 6.0,
                    status = "EXPIRING_SOON",
                ),
            ),
        )
    }
}
