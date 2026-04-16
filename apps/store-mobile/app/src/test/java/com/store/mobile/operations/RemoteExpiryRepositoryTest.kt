package com.store.mobile.operations

import com.store.mobile.controlplane.StoreMobileControlPlaneClient
import com.store.mobile.controlplane.StoreMobileControlPlaneRequest
import com.store.mobile.controlplane.StoreMobileControlPlaneResponse
import com.store.mobile.controlplane.StoreMobileControlPlaneTransport
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class RemoteExpiryRepositoryTest {
    @Test
    fun mapsExpiryReportIntoMobileReport() {
        val repository = RemoteExpiryRepository(
            tenantId = "tenant-demo-1",
            client = buildClient(),
        )

        val report = repository.loadExpiryReport(branchId = "branch-demo-1")

        assertEquals("branch-demo-1", report.branchId)
        assertEquals(1, report.trackedLotCount)
        assertEquals("ACME TEA", report.records.first().productName)
        assertEquals(6.0, report.records.first().remainingQuantity, 0.001)
    }

    @Test
    fun mapsRemoteExpiryLifecycle() {
        val repository = RemoteExpiryRepository(
            tenantId = "tenant-demo-1",
            client = buildClient(),
        )

        val board = repository.loadExpiryBoard(branchId = "branch-demo-1")
        assertEquals(1, board.openCount)
        assertEquals("EXP-BRANCHDEMO1-0001", board.records.first().sessionNumber)

        val createdSession = repository.createExpirySession(
            branchId = "branch-demo-1",
            batchLotId = "batch-1",
            note = "Shelf review before disposal",
        )
        assertEquals("OPEN", createdSession.status)
        assertEquals("ACME TEA", createdSession.productName)
        assertEquals("BATCH-EXP-1", createdSession.batchNumber)

        val reviewedSession = repository.recordExpiryReview(
            branchId = "branch-demo-1",
            sessionId = "bes-1",
            proposedQuantity = 1.0,
            reason = "Expired on shelf",
            note = "Front shelf pouch damaged",
        )
        assertEquals("REVIEWED", reviewedSession.status)
        assertEquals(1.0, reviewedSession.proposedQuantity ?: 0.0, 0.001)
        assertEquals("Expired on shelf", reviewedSession.reason)

        val approval = repository.approveExpirySession(
            branchId = "branch-demo-1",
            sessionId = "bes-1",
            reviewNote = "Approved after shelf check",
        )
        assertEquals("APPROVED", approval.session.status)
        assertEquals(1.0, approval.writeOff.writeOffQuantity, 0.001)
        assertEquals(
            "Approved after shelf check",
            repository.latestApprovedWriteOff(branchId = "branch-demo-1")?.session?.reviewNote,
        )

        val canceledSession = repository.cancelExpirySession(
            branchId = "branch-demo-1",
            sessionId = "bes-2",
            reviewNote = "Transfer to QA review instead",
        )
        assertEquals("CANCELED", canceledSession.status)
        assertEquals("ACME TEA", canceledSession.productName)
        assertNull(canceledSession.proposedQuantity)
    }

    private fun buildClient(): StoreMobileControlPlaneClient {
        return StoreMobileControlPlaneClient(
            baseUrl = "http://127.0.0.1:9400",
            accessToken = "session-token",
            transport = FakeRemoteExpiryTransport(),
        )
    }
}

private class FakeRemoteExpiryTransport : StoreMobileControlPlaneTransport {
    override fun execute(request: StoreMobileControlPlaneRequest): StoreMobileControlPlaneResponse {
        val body = when (request.path) {
            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/batch-expiry-report" ->
                """
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
                """.trimIndent()

            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/batch-expiry-board" ->
                """
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
                """.trimIndent()

            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/batch-expiry-sessions" ->
                """
                    {
                      "id": "bes-1",
                      "tenant_id": "tenant-demo-1",
                      "branch_id": "branch-demo-1",
                      "batch_lot_id": "batch-1",
                      "product_id": "prod-demo-1",
                      "session_number": "EXP-BRANCHDEMO1-0001",
                      "status": "OPEN",
                      "remaining_quantity_snapshot": 6.0,
                      "proposed_quantity": null,
                      "reason": null,
                      "note": "Shelf review before disposal",
                      "review_note": null
                    }
                """.trimIndent()

            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/batch-expiry-sessions/bes-1/review" ->
                """
                    {
                      "id": "bes-1",
                      "tenant_id": "tenant-demo-1",
                      "branch_id": "branch-demo-1",
                      "batch_lot_id": "batch-1",
                      "product_id": "prod-demo-1",
                      "session_number": "EXP-BRANCHDEMO1-0001",
                      "status": "REVIEWED",
                      "remaining_quantity_snapshot": 6.0,
                      "proposed_quantity": 1.0,
                      "reason": "Expired on shelf",
                      "note": "Shelf review before disposal",
                      "review_note": null
                    }
                """.trimIndent()

            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/batch-expiry-sessions/bes-1/approve" ->
                """
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
                """.trimIndent()

            "/v1/tenants/tenant-demo-1/branches/branch-demo-1/batch-expiry-sessions/bes-2/cancel" ->
                """
                    {
                      "id": "bes-2",
                      "tenant_id": "tenant-demo-1",
                      "branch_id": "branch-demo-1",
                      "batch_lot_id": "batch-1",
                      "product_id": "prod-demo-1",
                      "session_number": "EXP-BRANCHDEMO1-0002",
                      "status": "CANCELED",
                      "remaining_quantity_snapshot": 6.0,
                      "proposed_quantity": null,
                      "reason": null,
                      "note": "Shelf review before disposal",
                      "review_note": "Transfer to QA review instead"
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
