package com.store.mobile.operations

import com.store.mobile.controlplane.StoreMobileControlPlaneClient
import com.store.mobile.controlplane.StoreMobileControlPlaneRequest
import com.store.mobile.controlplane.StoreMobileControlPlaneResponse
import com.store.mobile.controlplane.StoreMobileControlPlaneTransport
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class RemoteStockCountRepositoryTest {
    @Test
    fun mapsInventorySnapshotIntoStockCountContext() {
        val repository = RemoteStockCountRepository(
            tenantId = "tenant-demo-1",
            client = buildClient(),
        )

        val context = repository.loadStockCountContext(branchId = "branch-demo-1")

        assertEquals("branch-demo-1", context.branchId)
        assertEquals(2, context.records.size)
        assertEquals("ACME TEA", context.records.first().productName)
        assertEquals(18.0, context.records.first().expectedQuantity, 0.001)
    }

    @Test
    fun mapsRemoteReviewedStockCountLifecycle() {
        val repository = RemoteStockCountRepository(
            tenantId = "tenant-demo-1",
            client = buildClient(),
        )

        val board = repository.loadStockCountBoard(branchId = "branch-demo-1")
        assertEquals(1, board.openCount)
        assertEquals("SCNT-BRANCHDEMO1-0001", board.records.first().sessionNumber)

        val createdSession = repository.createStockCountSession(
            branchId = "branch-demo-1",
            productId = "prod-demo-1",
            note = "Blind count before aisle reset",
        )
        assertEquals("OPEN", createdSession.status)
        assertEquals("ACME TEA", createdSession.productName)
        assertNull(createdSession.expectedQuantity)

        val countedSession = repository.recordBlindCount(
            branchId = "branch-demo-1",
            sessionId = "scs-1",
            countedQuantity = 16.0,
            note = "Two boxes missing from front shelf",
        )
        assertEquals("COUNTED", countedSession.status)
        assertEquals(-2.0, countedSession.varianceQuantity ?: 0.0, 0.001)
        assertEquals("ACME TEA", countedSession.productName)

        val approval = repository.approveCountSession(
            branchId = "branch-demo-1",
            sessionId = "scs-1",
            reviewNote = "Variance accepted after aisle check",
        )
        assertEquals("APPROVED", approval.session.status)
        assertEquals(16.0, approval.stockCount.closingStock, 0.001)
        assertEquals(
            "Variance accepted after aisle check",
            repository.latestApprovedCount(branchId = "branch-demo-1")?.session?.reviewNote,
        )

        val canceledSession = repository.cancelCountSession(
            branchId = "branch-demo-1",
            sessionId = "scs-2",
            reviewNote = "Scanner recount requested",
        )
        assertEquals("CANCELED", canceledSession.status)
        assertEquals("GINGER TEA", canceledSession.productName)
    }

    private fun buildClient(): StoreMobileControlPlaneClient {
        return StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = FakeRemoteStockCountTransport(),
        )
    }
}

private class FakeRemoteStockCountTransport : StoreMobileControlPlaneTransport {
    override fun execute(request: StoreMobileControlPlaneRequest): StoreMobileControlPlaneResponse {
        val body = when (request.path) {
            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/inventory-snapshot" ->
                """
                    {
                      "records": [
                        {
                          "product_id": "prod-demo-1",
                          "product_name": "ACME TEA",
                          "sku_code": "TEA-001",
                          "stock_on_hand": 18.0,
                          "last_entry_type": "goods_receipt"
                        },
                        {
                          "product_id": "prod-demo-2",
                          "product_name": "GINGER TEA",
                          "sku_code": "TEA-002",
                          "stock_on_hand": 10.0,
                          "last_entry_type": "stock_adjustment"
                        }
                      ]
                    }
                """.trimIndent()

            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/stock-count-board" ->
                """
                    {
                      "branch_id": "branch-demo-1",
                      "open_count": 1,
                      "counted_count": 0,
                      "approved_count": 0,
                      "canceled_count": 0,
                      "records": [
                        {
                          "stock_count_session_id": "scs-1",
                          "session_number": "SCNT-BRANCHDEMO1-0001",
                          "product_id": "prod-demo-1",
                          "product_name": "ACME TEA",
                          "sku_code": "TEA-001",
                          "status": "OPEN",
                          "expected_quantity": null,
                          "counted_quantity": null,
                          "variance_quantity": null,
                          "note": "Blind count before aisle reset",
                          "review_note": null
                        }
                      ]
                    }
                """.trimIndent()

            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/stock-count-sessions" ->
                """
                    {
                      "id": "scs-1",
                      "tenant_id": "tenant-demo-1",
                      "branch_id": "branch-demo-1",
                      "product_id": "prod-demo-1",
                      "session_number": "SCNT-BRANCHDEMO1-0001",
                      "status": "OPEN",
                      "expected_quantity": null,
                      "counted_quantity": null,
                      "variance_quantity": null,
                      "note": "Blind count before aisle reset",
                      "review_note": null
                    }
                """.trimIndent()

            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/stock-count-sessions/scs-1/record" ->
                """
                    {
                      "id": "scs-1",
                      "tenant_id": "tenant-demo-1",
                      "branch_id": "branch-demo-1",
                      "product_id": "prod-demo-1",
                      "session_number": "SCNT-BRANCHDEMO1-0001",
                      "status": "COUNTED",
                      "expected_quantity": 18.0,
                      "counted_quantity": 16.0,
                      "variance_quantity": -2.0,
                      "note": "Two boxes missing from front shelf",
                      "review_note": null
                    }
                """.trimIndent()

            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/stock-count-sessions/scs-1/approve" ->
                """
                    {
                      "session": {
                        "id": "scs-1",
                        "tenant_id": "tenant-demo-1",
                        "branch_id": "branch-demo-1",
                        "product_id": "prod-demo-1",
                        "session_number": "SCNT-BRANCHDEMO1-0001",
                        "status": "APPROVED",
                        "expected_quantity": 18.0,
                        "counted_quantity": 16.0,
                        "variance_quantity": -2.0,
                        "note": "Two boxes missing from front shelf",
                        "review_note": "Variance accepted after aisle check"
                      },
                      "stock_count": {
                        "id": "count-1",
                        "tenant_id": "tenant-demo-1",
                        "branch_id": "branch-demo-1",
                        "product_id": "prod-demo-1",
                        "counted_quantity": 16.0,
                        "expected_quantity": 18.0,
                        "variance_quantity": -2.0,
                        "note": "Variance accepted after aisle check",
                        "closing_stock": 16.0
                      }
                    }
                """.trimIndent()

            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/stock-count-sessions/scs-2/cancel" ->
                """
                    {
                      "id": "scs-2",
                      "tenant_id": "tenant-demo-1",
                      "branch_id": "branch-demo-1",
                      "product_id": "prod-demo-2",
                      "session_number": "SCNT-BRANCHDEMO1-0002",
                      "status": "CANCELED",
                      "expected_quantity": null,
                      "counted_quantity": null,
                      "variance_quantity": null,
                      "note": null,
                      "review_note": "Scanner recount requested"
                    }
                """.trimIndent()

            else -> error("Unexpected request path: ${request.path}")
        }
        return StoreMobileControlPlaneResponse(
            statusCode = 200,
            body = body,
        )
    }
}
