package com.store.mobile.operations

import com.store.mobile.controlplane.ControlPlaneGoodsReceipt
import com.store.mobile.controlplane.ControlPlaneGoodsReceiptLineReceiveInput
import com.store.mobile.controlplane.ControlPlaneGoodsReceiptRecord
import com.store.mobile.controlplane.ControlPlanePurchaseOrder
import com.store.mobile.controlplane.StoreMobileControlPlaneClient
import com.store.mobile.controlplane.StoreMobileControlPlaneException

class RemoteReceivingRepository(
    private val tenantId: String,
    private val client: StoreMobileControlPlaneClient,
) : ReceivingRepository {
    private val draftCacheByBranch = mutableMapOf<String, ReceivingDraft?>()
    private val latestReceiptByBranch = mutableMapOf<String, ReviewedGoodsReceipt?>()

    override fun loadReceivingBoard(branchId: String): ReceivingBoard {
        return runControlPlane {
            val board = client.getReceivingBoard(tenantId = tenantId, branchId = branchId)
            draftCacheByBranch[branchId] = board.records.firstOrNull { it.canReceive }?.let { record ->
                mapPurchaseOrderToDraft(
                    purchaseOrder = client.getPurchaseOrder(
                        tenantId = tenantId,
                        branchId = branchId,
                        purchaseOrderId = record.purchaseOrderId,
                    ),
                    supplierName = record.supplierName,
                )
            }
            latestReceiptByBranch.putIfAbsent(
                branchId,
                client.listGoodsReceipts(tenantId = tenantId, branchId = branchId).records.lastOrNull()?.let(::mapReceiptSummary),
            )
            ReceivingBoard(
                branchId = board.branchId,
                readyCount = board.readyCount,
                receivedCount = board.receivedCount,
                receivedWithVarianceCount = board.receivedWithVarianceCount,
                records = board.records.map { record ->
                    ReceivingBoardRecord(
                        purchaseOrderId = record.purchaseOrderId,
                        purchaseOrderNumber = record.purchaseOrderNumber,
                        supplierName = record.supplierName,
                        receivingStatus = record.receivingStatus,
                        canReceive = record.canReceive,
                        hasDiscrepancy = record.hasDiscrepancy,
                        varianceQuantity = record.varianceQuantity,
                    )
                },
            )
        }
    }

    override fun loadReceivingDraft(branchId: String): ReceivingDraft? {
        return draftCacheByBranch[branchId] ?: loadReceivingBoard(branchId).let { draftCacheByBranch[branchId] }
    }

    override fun latestGoodsReceipt(branchId: String): ReviewedGoodsReceipt? {
        return latestReceiptByBranch[branchId]
    }

    override fun createReviewedReceipt(branchId: String, input: CreateReviewedReceiptInput): ReviewedGoodsReceipt {
        return runControlPlane {
            val goodsReceipt = client.createGoodsReceipt(
                tenantId = tenantId,
                branchId = branchId,
                purchaseOrderId = input.purchaseOrderId,
                note = input.note,
                lines = input.lines.map { line ->
                    ControlPlaneGoodsReceiptLineReceiveInput(
                        productId = line.productId,
                        receivedQuantity = line.receivedQuantity,
                        discrepancyNote = line.discrepancyNote,
                    )
                },
            )
            val mapped = mapGoodsReceipt(goodsReceipt)
            latestReceiptByBranch[branchId] = mapped
            draftCacheByBranch[branchId] = null
            mapped
        }
    }

    private fun mapPurchaseOrderToDraft(
        purchaseOrder: ControlPlanePurchaseOrder,
        supplierName: String,
    ): ReceivingDraft {
        return ReceivingDraft(
            purchaseOrderId = purchaseOrder.id,
            purchaseOrderNumber = purchaseOrder.purchaseOrderNumber,
            supplierName = supplierName,
            lines = purchaseOrder.lines.map { line ->
                ReceivingDraftLine(
                    productId = line.productId,
                    productName = line.productName,
                    skuCode = line.skuCode,
                    orderedQuantity = line.quantity,
                )
            },
        )
    }

    private fun mapGoodsReceipt(goodsReceipt: ControlPlaneGoodsReceipt): ReviewedGoodsReceipt {
        return ReviewedGoodsReceipt(
            goodsReceiptId = goodsReceipt.id,
            goodsReceiptNumber = goodsReceipt.goodsReceiptNumber,
            purchaseOrderId = goodsReceipt.purchaseOrderId,
            receivedOn = goodsReceipt.receivedOn,
            note = goodsReceipt.note,
            receivedQuantityTotal = goodsReceipt.receivedQuantityTotal,
            varianceQuantityTotal = goodsReceipt.varianceQuantityTotal,
            hasDiscrepancy = goodsReceipt.hasDiscrepancy,
            lines = goodsReceipt.lines.map { line ->
                ReviewedGoodsReceiptLine(
                    productId = line.productId,
                    productName = line.productName,
                    skuCode = line.skuCode,
                    orderedQuantity = line.orderedQuantity,
                    quantity = line.quantity,
                    varianceQuantity = line.varianceQuantity,
                    discrepancyNote = line.discrepancyNote,
                )
            },
        )
    }

    private fun mapReceiptSummary(record: ControlPlaneGoodsReceiptRecord): ReviewedGoodsReceipt {
        return ReviewedGoodsReceipt(
            goodsReceiptId = record.goodsReceiptId,
            goodsReceiptNumber = record.goodsReceiptNumber,
            purchaseOrderId = record.purchaseOrderId,
            receivedOn = record.receivedOn,
            note = record.note,
            receivedQuantityTotal = record.receivedQuantity,
            varianceQuantityTotal = record.varianceQuantity,
            hasDiscrepancy = record.hasDiscrepancy,
            lines = emptyList(),
        )
    }

    private fun <T> runControlPlane(action: () -> T): T {
        return try {
            action()
        } catch (error: StoreMobileControlPlaneException) {
            throw IllegalArgumentException(error.message ?: "Control-plane request failed.")
        }
    }
}
