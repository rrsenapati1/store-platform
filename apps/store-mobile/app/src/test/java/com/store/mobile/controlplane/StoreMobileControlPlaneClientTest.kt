package com.store.mobile.controlplane

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class StoreMobileControlPlaneClientTest {
    @Test
    fun getsCatalogScanWithPolicyFields() {
        val transport = FakeStoreMobileControlPlaneTransport(
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
        )
        val client = StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = transport,
        )

        val lookup = client.lookupCatalogScan(
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
            barcode = " 1234567890123 ",
        )

        assertEquals(
            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/catalog-scan/1234567890123",
            transport.lastRequest?.path,
        )
        assertEquals("Bearer session-token", transport.lastRequest?.authorizationHeader)
        assertEquals("prod-demo-1", lookup?.productId)
        assertEquals(10.0, lookup?.reorderPoint ?: 0.0, 0.001)
        assertEquals(24.0, lookup?.targetStock ?: 0.0, 0.001)
    }

    @Test
    fun returnsNullForCatalogScanNotFound() {
        val transport = FakeStoreMobileControlPlaneTransport(
            responseBody = """{"detail":"Catalog barcode not found"}""",
            statusCode = 404,
        )
        val client = StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = transport,
        )

        val lookup = client.lookupCatalogScan(
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
            barcode = "1234567890123",
        )

        assertNull(lookup)
    }

    @Test
    fun getsStockCountBoardWithBearerAuthAndBranchPath() {
        val transport = FakeStoreMobileControlPlaneTransport(
            responseBody = """
                {
                  "branch_id": "branch-demo-1",
                  "open_count": 1,
                  "counted_count": 0,
                  "approved_count": 2,
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
            """.trimIndent(),
        )
        val client = StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = transport,
        )

        val board = client.getStockCountBoard(tenantId = "tenant-demo-1", branchId = "branch-demo-1")

        assertEquals(
            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/stock-count-board",
            transport.lastRequest?.path,
        )
        assertEquals("Bearer session-token", transport.lastRequest?.authorizationHeader)
        assertEquals("branch-demo-1", board.branchId)
        assertEquals("SCNT-BRANCHDEMO1-0001", board.records.first().sessionNumber)
    }

    @Test
    fun postsRecordBlindCountPayload() {
        val transport = FakeStoreMobileControlPlaneTransport(
            responseBody = """
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
            """.trimIndent(),
        )
        val client = StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = transport,
        )

        val session = client.recordStockCountSession(
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
            stockCountSessionId = "scs-1",
            countedQuantity = 16.0,
            note = "Two boxes missing from front shelf",
        )

        assertEquals("POST", transport.lastRequest?.method)
        assertEquals(
            """{"counted_quantity":16.0,"note":"Two boxes missing from front shelf"}""",
            transport.lastRequest?.body,
        )
        assertEquals("COUNTED", session.status)
        assertEquals(-2.0, session.varianceQuantity ?: 0.0, 0.001)
    }

    @Test
    fun getsReceivingBoardWithApprovedPurchaseOrderPosture() {
        val transport = FakeStoreMobileControlPlaneTransport(
            responseBody = """
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
            """.trimIndent(),
        )
        val client = StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = transport,
        )

        val board = client.getReceivingBoard(tenantId = "tenant-demo-1", branchId = "branch-demo-1")

        assertEquals(
            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/receiving-board",
            transport.lastRequest?.path,
        )
        assertEquals(1, board.readyCount)
        assertEquals("PO-001", board.records.first().purchaseOrderNumber)
    }

    @Test
    fun getsPurchaseOrderDetailWithLineItems() {
        val transport = FakeStoreMobileControlPlaneTransport(
            responseBody = """
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
            """.trimIndent(),
        )
        val client = StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = transport,
        )

        val purchaseOrder = client.getPurchaseOrder(
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
            purchaseOrderId = "po-1",
        )

        assertEquals(
            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/purchase-orders/po-1",
            transport.lastRequest?.path,
        )
        assertEquals("PO-001", purchaseOrder.purchaseOrderNumber)
        assertEquals("GINGER TEA", purchaseOrder.lines.last().productName)
    }

    @Test
    fun postsReviewedGoodsReceiptPayload() {
        val transport = FakeStoreMobileControlPlaneTransport(
            responseBody = """
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
            """.trimIndent(),
        )
        val client = StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = transport,
        )

        val goodsReceipt = client.createGoodsReceipt(
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
            purchaseOrderId = "po-1",
            note = "Second product held back pending supplier replacement",
            lines = listOf(
                ControlPlaneGoodsReceiptLineReceiveInput(
                    productId = "prod-demo-1",
                    receivedQuantity = 20.0,
                    discrepancyNote = "Four cartons short",
                ),
                ControlPlaneGoodsReceiptLineReceiveInput(
                    productId = "prod-demo-2",
                    receivedQuantity = 0.0,
                    discrepancyNote = "Supplier held dispatch",
                ),
            ),
        )

        assertEquals("POST", transport.lastRequest?.method)
        assertEquals(
            """{"purchase_order_id":"po-1","note":"Second product held back pending supplier replacement","lines":[{"product_id":"prod-demo-1","received_quantity":20.0,"discrepancy_note":"Four cartons short"},{"product_id":"prod-demo-2","received_quantity":0.0,"discrepancy_note":"Supplier held dispatch"}]}""",
            transport.lastRequest?.body,
        )
        assertEquals("GRN-BRANCHDEMO1-0001", goodsReceipt.goodsReceiptNumber)
        assertEquals(14.0, goodsReceipt.varianceQuantityTotal, 0.001)
    }

    @Test
    fun getsBatchExpiryReportWithTrackedLots() {
        val transport = FakeStoreMobileControlPlaneTransport(
            responseBody = """
                {
                  "branch_id": "branch-demo-1",
                  "tracked_lot_count": 1,
                  "expiring_soon_count": 1,
                  "expired_count": 0,
                  "untracked_stock_quantity": 0.0,
                  "records": [
                    {
                      "batch_lot_id": "batch-1",
                      "product_id": "prod-demo-1",
                      "product_name": "ACME TEA",
                      "batch_number": "BATCH-EXP-1",
                      "expiry_date": "2026-05-20",
                      "days_to_expiry": 7,
                      "received_quantity": 6.0,
                      "written_off_quantity": 0.0,
                      "remaining_quantity": 6.0,
                      "status": "EXPIRING_SOON"
                    }
                  ]
                }
            """.trimIndent(),
        )
        val client = StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = transport,
        )

        val report = client.getBatchExpiryReport(tenantId = "tenant-demo-1", branchId = "branch-demo-1")

        assertEquals(
            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/batch-expiry-report",
            transport.lastRequest?.path,
        )
        assertEquals(1, report.trackedLotCount)
        assertEquals("BATCH-EXP-1", report.records.first().batchNumber)
    }

    @Test
    fun getsBatchExpiryBoardWithOpenSession() {
        val transport = FakeStoreMobileControlPlaneTransport(
            responseBody = """
                {
                  "branch_id": "branch-demo-1",
                  "open_count": 1,
                  "reviewed_count": 0,
                  "approved_count": 0,
                  "canceled_count": 0,
                  "records": [
                    {
                      "batch_expiry_session_id": "bes-1",
                      "session_number": "EXP-BRANCHDEMO1-0001",
                      "batch_lot_id": "batch-1",
                      "product_id": "prod-demo-1",
                      "product_name": "ACME TEA",
                      "sku_code": "TEA-001",
                      "batch_number": "BATCH-EXP-1",
                      "status": "OPEN",
                      "remaining_quantity_snapshot": 6.0,
                      "proposed_quantity": null,
                      "reason": null,
                      "note": "Shelf review before disposal",
                      "review_note": null
                    }
                  ]
                }
            """.trimIndent(),
        )
        val client = StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = transport,
        )

        val board = client.getBatchExpiryBoard(tenantId = "tenant-demo-1", branchId = "branch-demo-1")

        assertEquals(
            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/batch-expiry-board",
            transport.lastRequest?.path,
        )
        assertEquals(1, board.openCount)
        assertEquals("EXP-BRANCHDEMO1-0001", board.records.first().sessionNumber)
    }

    @Test
    fun postsExpiryApprovalPayloadAndMapsWriteOff() {
        val transport = FakeStoreMobileControlPlaneTransport(
            responseBody = """
                {
                  "session": {
                    "id": "bes-1",
                    "tenant_id": "tenant-demo-1",
                    "branch_id": "branch-demo-1",
                    "batch_lot_id": "batch-1",
                    "product_id": "prod-demo-1",
                    "session_number": "EXP-BRANCHDEMO1-0001",
                    "status": "APPROVED",
                    "remaining_quantity_snapshot": 6.0,
                    "proposed_quantity": 1.0,
                    "reason": "Expired on shelf",
                    "note": "Shelf review before disposal",
                    "review_note": "Approved after shelf check"
                  },
                  "write_off": {
                    "batch_lot_id": "batch-1",
                    "product_id": "prod-demo-1",
                    "product_name": "ACME TEA",
                    "batch_number": "BATCH-EXP-1",
                    "expiry_date": "2026-05-20",
                    "received_quantity": 6.0,
                    "written_off_quantity": 1.0,
                    "remaining_quantity": 5.0,
                    "status": "EXPIRING_SOON",
                    "reason": "Expired on shelf"
                  }
                }
            """.trimIndent(),
        )
        val client = StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = transport,
        )

        val approval = client.approveBatchExpirySession(
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
            batchExpirySessionId = "bes-1",
            reviewNote = "Approved after shelf check",
        )

        assertEquals("POST", transport.lastRequest?.method)
        assertEquals(
            """{"review_note":"Approved after shelf check"}""",
            transport.lastRequest?.body,
        )
        assertEquals("APPROVED", approval.session.status)
        assertEquals(1.0, approval.writeOff.writtenOffQuantity, 0.001)
        assertEquals("BATCH-EXP-1", approval.writeOff.batchNumber)
    }

    @Test
    fun getsRestockBoardWithTrackedTask() {
        val transport = FakeStoreMobileControlPlaneTransport(
            responseBody = """
                {
                  "branch_id": "branch-demo-1",
                  "open_count": 1,
                  "picked_count": 0,
                  "completed_count": 0,
                  "canceled_count": 0,
                  "records": [
                    {
                      "restock_task_id": "rst-1",
                      "task_number": "RST-BRANCHDEMO1-0001",
                      "product_id": "prod-demo-1",
                      "product_name": "ACME TEA",
                      "sku_code": "TEA-001",
                      "status": "OPEN",
                      "stock_on_hand_snapshot": 8.0,
                      "reorder_point_snapshot": 10.0,
                      "target_stock_snapshot": 24.0,
                      "suggested_quantity_snapshot": 16.0,
                      "requested_quantity": 12.0,
                      "picked_quantity": null,
                      "source_posture": "BACKROOM_AVAILABLE",
                      "note": "Front shelf refill",
                      "completion_note": null,
                      "has_active_task": true
                    }
                  ]
                }
            """.trimIndent(),
        )
        val client = StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = transport,
        )

        val board = client.getRestockBoard(tenantId = "tenant-demo-1", branchId = "branch-demo-1")

        assertEquals(
            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/restock-board",
            transport.lastRequest?.path,
        )
        assertEquals(1, board.openCount)
        assertEquals("RST-BRANCHDEMO1-0001", board.records.first().taskNumber)
    }

    @Test
    fun postsCreateRestockTaskPayload() {
        val transport = FakeStoreMobileControlPlaneTransport(
            responseBody = """
                {
                  "id": "rst-1",
                  "tenant_id": "tenant-demo-1",
                  "branch_id": "branch-demo-1",
                  "product_id": "prod-demo-1",
                  "task_number": "RST-BRANCHDEMO1-0001",
                  "status": "OPEN",
                  "stock_on_hand_snapshot": 8.0,
                  "reorder_point_snapshot": 10.0,
                  "target_stock_snapshot": 24.0,
                  "suggested_quantity_snapshot": 16.0,
                  "requested_quantity": 12.0,
                  "picked_quantity": null,
                  "source_posture": "BACKROOM_AVAILABLE",
                  "note": "Front shelf refill",
                  "completion_note": null
                }
            """.trimIndent(),
        )
        val client = StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = transport,
        )

        val task = client.createRestockTask(
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
            productId = "prod-demo-1",
            requestedQuantity = 12.0,
            sourcePosture = "BACKROOM_AVAILABLE",
            note = "Front shelf refill",
        )

        assertEquals("POST", transport.lastRequest?.method)
        assertEquals(
            """{"product_id":"prod-demo-1","requested_quantity":12.0,"source_posture":"BACKROOM_AVAILABLE","note":"Front shelf refill"}""",
            transport.lastRequest?.body,
        )
        assertEquals("OPEN", task.status)
        assertEquals(16.0, task.suggestedQuantitySnapshot, 0.001)
    }

    @Test
    fun postsPickRestockTaskPayload() {
        val transport = FakeStoreMobileControlPlaneTransport(
            responseBody = """
                {
                  "id": "rst-1",
                  "tenant_id": "tenant-demo-1",
                  "branch_id": "branch-demo-1",
                  "product_id": "prod-demo-1",
                  "task_number": "RST-BRANCHDEMO1-0001",
                  "status": "PICKED",
                  "stock_on_hand_snapshot": 8.0,
                  "reorder_point_snapshot": 10.0,
                  "target_stock_snapshot": 24.0,
                  "suggested_quantity_snapshot": 16.0,
                  "requested_quantity": 12.0,
                  "picked_quantity": 10.0,
                  "source_posture": "BACKROOM_AVAILABLE",
                  "note": "Picked from backroom rack A",
                  "completion_note": null
                }
            """.trimIndent(),
        )
        val client = StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = transport,
        )

        val task = client.pickRestockTask(
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
            restockTaskId = "rst-1",
            pickedQuantity = 10.0,
            note = "Picked from backroom rack A",
        )

        assertEquals("POST", transport.lastRequest?.method)
        assertEquals(
            """{"picked_quantity":10.0,"note":"Picked from backroom rack A"}""",
            transport.lastRequest?.body,
        )
        assertEquals("PICKED", task.status)
        assertEquals(10.0, task.pickedQuantity ?: 0.0, 0.001)
    }

    @Test
    fun postsCompleteRestockTaskPayload() {
        val transport = FakeStoreMobileControlPlaneTransport(
            responseBody = """
                {
                  "id": "rst-1",
                  "tenant_id": "tenant-demo-1",
                  "branch_id": "branch-demo-1",
                  "product_id": "prod-demo-1",
                  "task_number": "RST-BRANCHDEMO1-0001",
                  "status": "COMPLETED",
                  "stock_on_hand_snapshot": 8.0,
                  "reorder_point_snapshot": 10.0,
                  "target_stock_snapshot": 24.0,
                  "suggested_quantity_snapshot": 16.0,
                  "requested_quantity": 12.0,
                  "picked_quantity": 10.0,
                  "source_posture": "BACKROOM_AVAILABLE",
                  "note": "Picked from backroom rack A",
                  "completion_note": "Shelf filled before rush hour"
                }
            """.trimIndent(),
        )
        val client = StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = transport,
        )

        val task = client.completeRestockTask(
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
            restockTaskId = "rst-1",
            completionNote = "Shelf filled before rush hour",
        )

        assertEquals("POST", transport.lastRequest?.method)
        assertEquals(
            """{"completion_note":"Shelf filled before rush hour"}""",
            transport.lastRequest?.body,
        )
        assertEquals("COMPLETED", task.status)
        assertEquals("Shelf filled before rush hour", task.completionNote)
    }

    @Test
    fun postsCancelRestockTaskPayload() {
        val transport = FakeStoreMobileControlPlaneTransport(
            responseBody = """
                {
                  "id": "rst-2",
                  "tenant_id": "tenant-demo-1",
                  "branch_id": "branch-demo-1",
                  "product_id": "prod-demo-1",
                  "task_number": "RST-BRANCHDEMO1-0002",
                  "status": "CANCELED",
                  "stock_on_hand_snapshot": 8.0,
                  "reorder_point_snapshot": 10.0,
                  "target_stock_snapshot": 24.0,
                  "suggested_quantity_snapshot": 16.0,
                  "requested_quantity": 6.0,
                  "picked_quantity": null,
                  "source_posture": "BACKROOM_AVAILABLE",
                  "note": "Second attempt",
                  "completion_note": "Transfer to QA review instead"
                }
            """.trimIndent(),
        )
        val client = StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = transport,
        )

        val task = client.cancelRestockTask(
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
            restockTaskId = "rst-2",
            cancelNote = "Transfer to QA review instead",
        )

        assertEquals("POST", transport.lastRequest?.method)
        assertEquals(
            """{"cancel_note":"Transfer to QA review instead"}""",
            transport.lastRequest?.body,
        )
        assertEquals("CANCELED", task.status)
        assertEquals("Transfer to QA review instead", task.completionNote)
    }
}

private class FakeStoreMobileControlPlaneTransport(
    private val responseBody: String,
    private val statusCode: Int = 200,
) : StoreMobileControlPlaneTransport {
    var lastRequest: StoreMobileControlPlaneRequest? = null

    override fun execute(request: StoreMobileControlPlaneRequest): StoreMobileControlPlaneResponse {
        lastRequest = request
        return StoreMobileControlPlaneResponse(
            statusCode = statusCode,
            body = responseBody,
        )
    }
}
