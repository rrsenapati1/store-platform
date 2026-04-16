package com.store.mobile.operations

import com.store.mobile.controlplane.StoreMobileControlPlaneClient
import com.store.mobile.controlplane.StoreMobileControlPlaneRequest
import com.store.mobile.controlplane.StoreMobileControlPlaneResponse
import com.store.mobile.controlplane.StoreMobileControlPlaneTransport
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class RemoteReceivingRepositoryTest {
    @Test
    fun mapsReceivingBoardAndApprovedPurchaseOrderIntoDraft() {
        val repository = RemoteReceivingRepository(
            tenantId = "tenant-demo-1",
            client = buildClient(),
        )

        val board = repository.loadReceivingBoard(branchId = "branch-demo-1")
        val draft = repository.loadReceivingDraft(branchId = "branch-demo-1")

        assertEquals("branch-demo-1", board.branchId)
        assertEquals(1, board.readyCount)
        assertEquals("PO-001", board.records.first().purchaseOrderNumber)
        assertEquals("PO-001", draft?.purchaseOrderNumber)
        assertEquals("Acme Wholesale", draft?.supplierName)
        assertEquals(2, draft?.lines?.size)
        assertEquals("GINGER TEA", draft?.lines?.last()?.productName)
        assertNull(repository.latestGoodsReceipt(branchId = "branch-demo-1"))
    }

    @Test
    fun createsReviewedGoodsReceiptAndCachesLatestReceipt() {
        val repository = RemoteReceivingRepository(
            tenantId = "tenant-demo-1",
            client = buildClient(),
        )

        val goodsReceipt = repository.createReviewedReceipt(
            branchId = "branch-demo-1",
            input = CreateReviewedReceiptInput(
                purchaseOrderId = "po-1",
                note = "Second product held back pending supplier replacement",
                lines = listOf(
                    ReviewedReceiptLineInput(
                        productId = "prod-demo-1",
                        receivedQuantity = 20.0,
                        discrepancyNote = "Four cartons short",
                    ),
                    ReviewedReceiptLineInput(
                        productId = "prod-demo-2",
                        receivedQuantity = 0.0,
                        discrepancyNote = "Supplier held dispatch",
                    ),
                ),
            ),
        )

        assertEquals("GRN-BRANCHDEMO1-0001", goodsReceipt.goodsReceiptNumber)
        assertTrue(goodsReceipt.hasDiscrepancy)
        assertEquals(2, goodsReceipt.lines.size)
        assertEquals(
            "Second product held back pending supplier replacement",
            repository.latestGoodsReceipt(branchId = "branch-demo-1")?.note,
        )
        assertEquals(
            14.0,
            repository.latestGoodsReceipt(branchId = "branch-demo-1")?.varianceQuantityTotal ?: 0.0,
            0.001,
        )
    }

    private fun buildClient(): StoreMobileControlPlaneClient {
        return StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = FakeRemoteReceivingTransport(),
        )
    }
}

private class FakeRemoteReceivingTransport : StoreMobileControlPlaneTransport {
    override fun execute(request: StoreMobileControlPlaneRequest): StoreMobileControlPlaneResponse {
        val body = when (request.path) {
            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/receiving-board" ->
                """
                    {
                      "branch_id": "branch-demo-1",
                      "blocked_count": 0,
                      "ready_count": 1,
                      "received_count": 0,
                      "received_with_variance_count": 0,
                      "records": [
                        {
                          "purchase_order_id": "po-1",
                          "purchase_order_number": "PO-001",
                          "supplier_name": "Acme Wholesale",
                          "approval_status": "APPROVED",
                          "receiving_status": "READY",
                          "can_receive": true,
                          "has_discrepancy": false,
                          "variance_quantity": 0.0,
                          "blocked_reason": null,
                          "goods_receipt_id": null
                        }
                      ]
                    }
                """.trimIndent()

            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/purchase-orders/po-1" ->
                """
                    {
                      "id": "po-1",
                      "tenant_id": "tenant-demo-1",
                      "branch_id": "branch-demo-1",
                      "supplier_id": "supplier-1",
                      "purchase_order_number": "PO-001",
                      "approval_status": "APPROVED",
                      "subtotal": 1700.0,
                      "tax_total": 306.0,
                      "grand_total": 2006.0,
                      "lines": [
                        {
                          "product_id": "prod-demo-1",
                          "product_name": "ACME TEA",
                          "sku_code": "TEA-001",
                          "quantity": 24.0,
                          "unit_cost": 50.0,
                          "line_total": 1200.0
                        },
                        {
                          "product_id": "prod-demo-2",
                          "product_name": "GINGER TEA",
                          "sku_code": "TEA-002",
                          "quantity": 10.0,
                          "unit_cost": 50.0,
                          "line_total": 500.0
                        }
                      ]
                    }
                """.trimIndent()

            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/goods-receipts" -> {
                if (request.method == "GET") {
                    """
                        {
                          "records": []
                        }
                    """.trimIndent()
                } else {
                    """
                        {
                          "id": "grn-1",
                          "tenant_id": "tenant-demo-1",
                          "branch_id": "branch-demo-1",
                          "purchase_order_id": "po-1",
                          "supplier_id": "supplier-1",
                          "goods_receipt_number": "GRN-BRANCHDEMO1-0001",
                          "received_on": "2026-04-16",
                          "note": "Second product held back pending supplier replacement",
                          "ordered_quantity_total": 34.0,
                          "received_quantity_total": 20.0,
                          "variance_quantity_total": 14.0,
                          "has_discrepancy": true,
                          "lines": [
                            {
                              "product_id": "prod-demo-1",
                              "product_name": "ACME TEA",
                              "sku_code": "TEA-001",
                              "ordered_quantity": 24.0,
                              "quantity": 20.0,
                              "variance_quantity": 4.0,
                              "unit_cost": 50.0,
                              "line_total": 1000.0,
                              "discrepancy_note": "Four cartons short"
                            },
                            {
                              "product_id": "prod-demo-2",
                              "product_name": "GINGER TEA",
                              "sku_code": "TEA-002",
                              "ordered_quantity": 10.0,
                              "quantity": 0.0,
                              "variance_quantity": 10.0,
                              "unit_cost": 50.0,
                              "line_total": 0.0,
                              "discrepancy_note": "Supplier held dispatch"
                            }
                          ]
                        }
                    """.trimIndent()
                }
            }

            else -> error("Unexpected request path: ${request.path}")
        }
        return StoreMobileControlPlaneResponse(
            statusCode = 200,
            body = body,
        )
    }
}
