package com.store.mobile.operations

import com.store.mobile.controlplane.ControlPlaneStockCountApproval
import com.store.mobile.controlplane.ControlPlaneStockCountBoard
import com.store.mobile.controlplane.ControlPlaneStockCountBoardRecord
import com.store.mobile.controlplane.ControlPlaneStockCountReviewSession
import com.store.mobile.controlplane.StoreMobileControlPlaneClient
import com.store.mobile.controlplane.StoreMobileControlPlaneException

class RemoteStockCountRepository(
    private val tenantId: String,
    private val client: StoreMobileControlPlaneClient,
) : StockCountRepository {
    private val productCatalogByBranch = mutableMapOf<String, Map<String, StockCountRecord>>()
    private val latestApprovalByBranch = mutableMapOf<String, StockCountApproval?>()

    override fun loadStockCountContext(branchId: String): StockCountContext {
        return runControlPlane {
            val records = client.getInventorySnapshot(tenantId = tenantId, branchId = branchId).records.map { record ->
                StockCountRecord(
                    productId = record.productId,
                    productName = record.productName,
                    skuCode = record.skuCode,
                    expectedQuantity = record.stockOnHand,
                )
            }
            productCatalogByBranch[branchId] = records.associateBy { it.productId }
            StockCountContext(
                branchId = branchId,
                records = records,
            )
        }
    }

    override fun loadStockCountBoard(branchId: String): StockCountBoard {
        return runControlPlane {
            val board = client.getStockCountBoard(tenantId = tenantId, branchId = branchId)
            StockCountBoard(
                branchId = board.branchId,
                openCount = board.openCount,
                countedCount = board.countedCount,
                approvedCount = board.approvedCount,
                canceledCount = board.canceledCount,
                records = board.records.map(::mapBoardRecord),
            )
        }
    }

    override fun latestApprovedCount(branchId: String): StockCountApproval? {
        return latestApprovalByBranch[branchId]
    }

    override fun createStockCountSession(branchId: String, productId: String, note: String?): StockCountReviewSession {
        return runControlPlane {
            val session = client.createStockCountSession(
                tenantId = tenantId,
                branchId = branchId,
                productId = productId,
                note = note,
            )
            mapSession(branchId = branchId, session = session)
        }
    }

    override fun recordBlindCount(
        branchId: String,
        sessionId: String,
        countedQuantity: Double,
        note: String?,
    ): StockCountReviewSession {
        return runControlPlane {
            val session = client.recordStockCountSession(
                tenantId = tenantId,
                branchId = branchId,
                stockCountSessionId = sessionId,
                countedQuantity = countedQuantity,
                note = note,
            )
            mapSession(branchId = branchId, session = session)
        }
    }

    override fun approveCountSession(branchId: String, sessionId: String, reviewNote: String?): StockCountApproval {
        return runControlPlane {
            val approval = client.approveStockCountSession(
                tenantId = tenantId,
                branchId = branchId,
                stockCountSessionId = sessionId,
                reviewNote = reviewNote,
            )
            val mappedApproval = mapApproval(branchId = branchId, approval = approval)
            latestApprovalByBranch[branchId] = mappedApproval
            mappedApproval
        }
    }

    override fun cancelCountSession(branchId: String, sessionId: String, reviewNote: String?): StockCountReviewSession {
        return runControlPlane {
            val session = client.cancelStockCountSession(
                tenantId = tenantId,
                branchId = branchId,
                stockCountSessionId = sessionId,
                reviewNote = reviewNote,
            )
            mapSession(branchId = branchId, session = session)
        }
    }

    private fun mapBoardRecord(record: ControlPlaneStockCountBoardRecord): StockCountReviewSession {
        return StockCountReviewSession(
            id = record.stockCountSessionId,
            sessionNumber = record.sessionNumber,
            productId = record.productId,
            productName = record.productName,
            skuCode = record.skuCode,
            status = record.status,
            expectedQuantity = record.expectedQuantity,
            countedQuantity = record.countedQuantity,
            varianceQuantity = record.varianceQuantity,
            note = record.note,
            reviewNote = record.reviewNote,
        )
    }

    private fun mapSession(branchId: String, session: ControlPlaneStockCountReviewSession): StockCountReviewSession {
        val productRecord = requireProductRecord(branchId = branchId, productId = session.productId)
        return StockCountReviewSession(
            id = session.id,
            sessionNumber = session.sessionNumber,
            productId = session.productId,
            productName = productRecord.productName,
            skuCode = productRecord.skuCode,
            status = session.status,
            expectedQuantity = session.expectedQuantity,
            countedQuantity = session.countedQuantity,
            varianceQuantity = session.varianceQuantity,
            note = session.note,
            reviewNote = session.reviewNote,
        )
    }

    private fun mapApproval(branchId: String, approval: ControlPlaneStockCountApproval): StockCountApproval {
        return StockCountApproval(
            session = mapSession(branchId = branchId, session = approval.session),
            stockCount = ApprovedStockCount(
                id = approval.stockCount.id,
                sessionId = approval.session.id,
                productId = approval.stockCount.productId,
                countedQuantity = approval.stockCount.countedQuantity,
                expectedQuantity = approval.stockCount.expectedQuantity,
                varianceQuantity = approval.stockCount.varianceQuantity,
                closingStock = approval.stockCount.closingStock,
                note = approval.stockCount.note,
            ),
        )
    }

    private fun requireProductRecord(branchId: String, productId: String): StockCountRecord {
        val existingCatalog = productCatalogByBranch[branchId]
        if (existingCatalog != null && existingCatalog.containsKey(productId)) {
            return requireNotNull(existingCatalog[productId])
        }
        return loadStockCountContext(branchId = branchId).records.firstOrNull { it.productId == productId }
            ?: throw IllegalArgumentException("Unknown stock-count product for branch.")
    }

    private fun <T> runControlPlane(action: () -> T): T {
        return try {
            action()
        } catch (error: StoreMobileControlPlaneException) {
            throw IllegalArgumentException(error.message ?: "Control-plane request failed.")
        }
    }
}
