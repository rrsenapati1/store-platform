package com.store.mobile.scan

import com.store.mobile.controlplane.StoreMobileControlPlaneClient
import com.store.mobile.controlplane.StoreMobileControlPlaneException

class RemoteScanLookupRepository(
    private val tenantId: String,
    private val branchId: String,
    private val client: StoreMobileControlPlaneClient,
) : ScanLookupRepository {
    override fun lookupBarcode(barcode: String): ScanLookupRecord? {
        return try {
            client.lookupCatalogScan(
                tenantId = tenantId,
                branchId = branchId,
                barcode = barcode,
            )?.let { record ->
                ScanLookupRecord(
                    productId = record.productId,
                    productName = record.productName,
                    skuCode = record.skuCode,
                    barcode = record.barcode,
                    sellingPrice = record.sellingPrice,
                    stockOnHand = record.stockOnHand,
                    availabilityStatus = record.availabilityStatus,
                    reorderPoint = record.reorderPoint,
                    targetStock = record.targetStock,
                )
            }
        } catch (error: StoreMobileControlPlaneException) {
            throw IllegalArgumentException(error.message ?: "Control-plane request failed.")
        }
    }
}
