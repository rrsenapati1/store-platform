package com.store.mobile.operations

import com.store.mobile.controlplane.StoreMobileControlPlaneClient
import com.store.mobile.controlplane.StoreMobileControlPlaneRequest
import com.store.mobile.controlplane.StoreMobileControlPlaneResponse
import com.store.mobile.controlplane.StoreMobileControlPlaneTransport
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class RemoteRestockRepositoryTest {
    @Test
    fun mapsRestockBoardIntoMobileBoard() {
        val repository = RemoteRestockRepository(
            tenantId = "tenant-demo-1",
            client = buildClient(),
        )

        val board = repository.loadRestockBoard(branchId = "branch-demo-1")

        assertEquals("branch-demo-1", board.branchId)
        assertEquals(1, board.openCount)
        assertEquals("RST-BRANCHDEMO1-0001", board.records.first().taskNumber)
        assertEquals("ACME TEA", board.records.first().productName)
        assertEquals("rst-1", board.records.first().activeTaskId)
    }

    @Test
    fun mapsRemoteRestockLifecycle() {
        val repository = RemoteRestockRepository(
            tenantId = "tenant-demo-1",
            client = buildClient(),
        )

        val createdTask = repository.createRestockTask(
            branchId = "branch-demo-1",
            input = CreateRestockTaskInput(
                productId = "prod-demo-1",
                productName = "ACME TEA",
                skuCode = "TEA-001",
                stockOnHandSnapshot = 8.0,
                reorderPointSnapshot = 10.0,
                targetStockSnapshot = 24.0,
                requestedQuantity = 12.0,
                sourcePosture = "BACKROOM_AVAILABLE",
                note = "Front shelf refill",
            ),
        )
        assertEquals("OPEN", createdTask.status)
        assertEquals("ACME TEA", createdTask.productName)
        assertEquals("RST-BRANCHDEMO1-0001", createdTask.taskNumber)

        val pickedTask = repository.pickRestockTask(
            branchId = "branch-demo-1",
            taskId = "rst-1",
            pickedQuantity = 10.0,
            note = "Picked from backroom rack A",
        )
        assertEquals("PICKED", pickedTask.status)
        assertEquals(10.0, pickedTask.pickedQuantity ?: 0.0, 0.001)

        val completedTask = repository.completeRestockTask(
            branchId = "branch-demo-1",
            taskId = "rst-1",
            completionNote = "Shelf filled before rush hour",
        )
        assertEquals("COMPLETED", completedTask.status)
        assertEquals("Shelf filled before rush hour", completedTask.completionNote)

        val canceledTask = repository.cancelRestockTask(
            branchId = "branch-demo-1",
            taskId = "rst-2",
            cancelNote = "Transfer to QA review instead",
        )
        assertEquals("CANCELED", canceledTask.status)
        assertEquals("Transfer to QA review instead", canceledTask.completionNote)

        val board = repository.loadRestockBoard(branchId = "branch-demo-1")
        assertEquals(1, board.openCount)
        assertEquals("rst-1", board.records.first().activeTaskId)
        val completedRecord = board.records.firstOrNull { record -> record.status == "COMPLETED" }
        assertNull(completedRecord?.activeTaskId)
    }

    private fun buildClient(): StoreMobileControlPlaneClient {
        return StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = FakeRemoteRestockTransport(),
        )
    }
}

private class FakeRemoteRestockTransport : StoreMobileControlPlaneTransport {
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
                          "stock_on_hand": 8.0,
                          "last_entry_type": "goods_receipt"
                        }
                      ]
                    }
                """.trimIndent()

            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/restock-board" ->
                """
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
                """.trimIndent()

            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/restock-tasks" ->
                """
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
                """.trimIndent()

            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/restock-tasks/rst-1/pick" ->
                """
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
                """.trimIndent()

            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/restock-tasks/rst-1/complete" ->
                """
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
                """.trimIndent()

            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/restock-tasks/rst-2/cancel" ->
                """
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
                """.trimIndent()

            else -> error("Unexpected request path: ${request.path}")
        }
        return StoreMobileControlPlaneResponse(
            statusCode = 200,
            body = body,
        )
    }
}
