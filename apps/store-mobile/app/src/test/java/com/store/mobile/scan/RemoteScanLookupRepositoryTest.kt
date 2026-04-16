package com.store.mobile.scan

import com.store.mobile.controlplane.StoreMobileControlPlaneClient
import com.store.mobile.controlplane.StoreMobileControlPlaneRequest
import com.store.mobile.controlplane.StoreMobileControlPlaneResponse
import com.store.mobile.controlplane.StoreMobileControlPlaneTransport
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class RemoteScanLookupRepositoryTest {
    @Test
    fun mapsRemoteCatalogScanIntoLookupRecord() {
        val repository = RemoteScanLookupRepository(
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
            client = buildClient(
                responseBody = """
                    {
                      "product_id": "prod-demo-1",
                      "product_name": "ACME TEA",
                      "sku_code": "TEA-001",
                      "barcode": "1234567890123",
                      "selling_price": 125.0,
                      "stock_on_hand": 18.0,
                      "availability_status": "ACTIVE",
                      "reorder_point": 10.0,
                      "target_stock": 24.0
                    }
                """.trimIndent(),
            ),
        )

        val record = repository.lookupBarcode(" 1234567890123 ")

        requireNotNull(record)
        assertEquals("prod-demo-1", record.productId)
        assertEquals("ACME TEA", record.productName)
        assertEquals(10.0, record.reorderPoint ?: 0.0, 0.001)
        assertEquals(24.0, record.targetStock ?: 0.0, 0.001)
    }

    @Test
    fun mapsNullPolicyValues() {
        val repository = RemoteScanLookupRepository(
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
            client = buildClient(
                responseBody = """
                    {
                      "product_id": "prod-demo-1",
                      "product_name": "ACME TEA",
                      "sku_code": "TEA-001",
                      "barcode": "1234567890123",
                      "selling_price": 125.0,
                      "stock_on_hand": 18.0,
                      "availability_status": "ACTIVE",
                      "reorder_point": null,
                      "target_stock": null
                    }
                """.trimIndent(),
            ),
        )

        val record = repository.lookupBarcode("1234567890123")

        requireNotNull(record)
        assertNull(record.reorderPoint)
        assertNull(record.targetStock)
    }

    @Test
    fun returnsNullWhenCatalogScanIsNotFound() {
        val repository = RemoteScanLookupRepository(
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
            client = buildClient(
                responseBody = """{"detail":"Catalog barcode not found"}""",
                statusCode = 404,
            ),
        )

        val record = repository.lookupBarcode("1234567890123")

        assertNull(record)
    }

    private fun buildClient(
        responseBody: String,
        statusCode: Int = 200,
    ): StoreMobileControlPlaneClient {
        return StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = FakeRemoteScanLookupTransport(
                responseBody = responseBody,
                statusCode = statusCode,
            ),
        )
    }
}

private class FakeRemoteScanLookupTransport(
    private val responseBody: String,
    private val statusCode: Int,
) : StoreMobileControlPlaneTransport {
    override fun execute(request: StoreMobileControlPlaneRequest): StoreMobileControlPlaneResponse {
        return StoreMobileControlPlaneResponse(
            statusCode = statusCode,
            body = responseBody,
        )
    }
}
