package com.store.mobile.operations

import com.store.mobile.controlplane.ControlPlaneBatchExpiryApproval
import com.store.mobile.controlplane.ControlPlaneBatchExpiryBoard
import com.store.mobile.controlplane.ControlPlaneBatchExpiryBoardRecord
import com.store.mobile.controlplane.ControlPlaneBatchExpiryReport
import com.store.mobile.controlplane.ControlPlaneBatchExpiryReportRecord
import com.store.mobile.controlplane.ControlPlaneBatchExpiryReviewSession
import com.store.mobile.controlplane.StoreMobileControlPlaneClient
import com.store.mobile.controlplane.StoreMobileControlPlaneException

class RemoteExpiryRepository(
    private val tenantId: String,
    private val client: StoreMobileControlPlaneClient,
) : ExpiryRepository {
    private val reportCacheByBranch = mutableMapOf<String, ExpiryReport>()
    private val reportRecordCacheByBranch = mutableMapOf<String, Map<String, ExpiryRecord>>()
    private val latestApprovalByBranch = mutableMapOf<String, ExpiryReviewApproval?>()

    override fun loadExpiryReport(branchId: String): ExpiryReport {
        return runControlPlane {
            val report = mapReport(client.getBatchExpiryReport(tenantId = tenantId, branchId = branchId))
            cacheReport(branchId = branchId, report = report)
            report
        }
    }

    override fun loadExpiryBoard(branchId: String): ExpiryBoard {
        return runControlPlane {
            val board = client.getBatchExpiryBoard(tenantId = tenantId, branchId = branchId)
            ensureReportCache(branchId = branchId)
            ExpiryBoard(
                branchId = board.branchId,
                openCount = board.openCount,
                reviewedCount = board.reviewedCount,
                approvedCount = board.approvedCount,
                canceledCount = board.canceledCount,
                records = board.records.map { record -> mapBoardRecord(branchId = branchId, record = record) },
            )
        }
    }

    override fun latestApprovedWriteOff(branchId: String): ExpiryReviewApproval? {
        return latestApprovalByBranch[branchId]
    }

    override fun createExpirySession(branchId: String, batchLotId: String, note: String?): ExpiryReviewSession {
        return runControlPlane {
            ensureReportCache(branchId = branchId)
            val session = client.createBatchExpirySession(
                tenantId = tenantId,
                branchId = branchId,
                batchLotId = batchLotId,
                note = note,
            )
            mapSession(branchId = branchId, session = session)
        }
    }

    override fun recordExpiryReview(
        branchId: String,
        sessionId: String,
        proposedQuantity: Double,
        reason: String,
        note: String?,
    ): ExpiryReviewSession {
        return runControlPlane {
            val session = client.recordBatchExpirySession(
                tenantId = tenantId,
                branchId = branchId,
                batchExpirySessionId = sessionId,
                quantity = proposedQuantity,
                reason = reason,
            )
            mapSession(branchId = branchId, session = session).let { mapped ->
                if (!note.isNullOrBlank() && mapped.note.isNullOrBlank()) {
                    mapped.copy(note = note)
                } else {
                    mapped
                }
            }
        }
    }

    override fun approveExpirySession(branchId: String, sessionId: String, reviewNote: String?): ExpiryReviewApproval {
        return runControlPlane {
            val approval = client.approveBatchExpirySession(
                tenantId = tenantId,
                branchId = branchId,
                batchExpirySessionId = sessionId,
                reviewNote = reviewNote,
            )
            val mappedApproval = mapApproval(branchId = branchId, approval = approval)
            latestApprovalByBranch[branchId] = mappedApproval
            mappedApproval
        }
    }

    override fun cancelExpirySession(branchId: String, sessionId: String, reviewNote: String?): ExpiryReviewSession {
        return runControlPlane {
            val session = client.cancelBatchExpirySession(
                tenantId = tenantId,
                branchId = branchId,
                batchExpirySessionId = sessionId,
                reviewNote = reviewNote,
            )
            mapSession(branchId = branchId, session = session)
        }
    }

    private fun mapReport(report: ControlPlaneBatchExpiryReport): ExpiryReport {
        return ExpiryReport(
            branchId = report.branchId,
            trackedLotCount = report.trackedLotCount,
            expiringSoonCount = report.expiringSoonCount,
            expiredCount = report.expiredCount,
            records = report.records.map(::mapReportRecord),
        )
    }

    private fun mapReportRecord(record: ControlPlaneBatchExpiryReportRecord): ExpiryRecord {
        return ExpiryRecord(
            batchLotId = record.batchLotId,
            productName = record.productName,
            batchNumber = record.batchNumber,
            expiryDate = record.expiryDate,
            remainingQuantity = record.remainingQuantity,
            status = record.status,
        )
    }

    private fun mapBoardRecord(branchId: String, record: ControlPlaneBatchExpiryBoardRecord): ExpiryReviewSession {
        val reportRecord = requireReportRecord(branchId = branchId, batchLotId = record.batchLotId)
        return ExpiryReviewSession(
            id = record.batchExpirySessionId,
            sessionNumber = record.sessionNumber,
            batchLotId = record.batchLotId,
            productName = record.productName,
            batchNumber = record.batchNumber,
            expiryDate = reportRecord.expiryDate,
            status = record.status,
            remainingQuantitySnapshot = record.remainingQuantitySnapshot,
            proposedQuantity = record.proposedQuantity,
            reason = record.reason,
            note = record.note,
            reviewNote = record.reviewNote,
        )
    }

    private fun mapSession(branchId: String, session: ControlPlaneBatchExpiryReviewSession): ExpiryReviewSession {
        val reportRecord = requireReportRecord(branchId = branchId, batchLotId = session.batchLotId)
        return ExpiryReviewSession(
            id = session.id,
            sessionNumber = session.sessionNumber,
            batchLotId = session.batchLotId,
            productName = reportRecord.productName,
            batchNumber = reportRecord.batchNumber,
            expiryDate = reportRecord.expiryDate,
            status = session.status,
            remainingQuantitySnapshot = session.remainingQuantitySnapshot,
            proposedQuantity = session.proposedQuantity,
            reason = session.reason,
            note = session.note,
            reviewNote = session.reviewNote,
        )
    }

    private fun mapApproval(branchId: String, approval: ControlPlaneBatchExpiryApproval): ExpiryReviewApproval {
        val session = mapSession(branchId = branchId, session = approval.session)
        return ExpiryReviewApproval(
            session = session,
            writeOff = ApprovedExpiryWriteOff(
                id = "approved-expiry-write-off-${session.id}",
                sessionId = session.id,
                batchLotId = approval.writeOff.batchLotId,
                batchNumber = approval.writeOff.batchNumber,
                productName = approval.writeOff.productName,
                writeOffQuantity = approval.writeOff.writtenOffQuantity,
                remainingQuantityAfterWriteOff = approval.writeOff.remainingQuantity,
                statusAfterWriteOff = approval.writeOff.status,
                reason = approval.writeOff.reason,
                note = session.reviewNote ?: session.note,
            ),
        )
    }

    private fun ensureReportCache(branchId: String): ExpiryReport {
        return reportCacheByBranch[branchId] ?: loadExpiryReport(branchId = branchId)
    }

    private fun cacheReport(branchId: String, report: ExpiryReport) {
        reportCacheByBranch[branchId] = report
        reportRecordCacheByBranch[branchId] = report.records.associateBy { it.batchLotId }
    }

    private fun requireReportRecord(branchId: String, batchLotId: String): ExpiryRecord {
        val existing = reportRecordCacheByBranch[branchId]?.get(batchLotId)
        if (existing != null) {
            return existing
        }
        return ensureReportCache(branchId = branchId).records.firstOrNull { it.batchLotId == batchLotId }
            ?: throw IllegalArgumentException("Unknown expiry batch lot for branch.")
    }

    private fun <T> runControlPlane(action: () -> T): T {
        return try {
            action()
        } catch (error: StoreMobileControlPlaneException) {
            throw IllegalArgumentException(error.message ?: "Control-plane request failed.")
        }
    }
}
