package com.store.mobile.operations

import com.store.mobile.controlplane.ControlPlaneInventorySnapshotRecord
import com.store.mobile.controlplane.ControlPlaneRestockBoardRecord
import com.store.mobile.controlplane.ControlPlaneRestockTask
import com.store.mobile.controlplane.StoreMobileControlPlaneClient
import com.store.mobile.controlplane.StoreMobileControlPlaneException

class RemoteRestockRepository(
    private val tenantId: String,
    private val client: StoreMobileControlPlaneClient,
) : RestockRepository {
    private val productCatalogByBranch = mutableMapOf<String, Map<String, ControlPlaneInventorySnapshotRecord>>()
    private val taskMetadataByBranch = mutableMapOf<String, MutableMap<String, TaskMetadata>>()

    override fun loadRestockBoard(branchId: String): RestockBoard {
        return runControlPlane {
            val board = client.getRestockBoard(tenantId = tenantId, branchId = branchId)
            val metadataByTaskId = taskMetadataByBranch.getOrPut(branchId) { mutableMapOf() }
            board.records.forEach { record ->
                metadataByTaskId[record.restockTaskId] = TaskMetadata(
                    productName = record.productName,
                    skuCode = record.skuCode,
                )
            }
            RestockBoard(
                branchId = board.branchId,
                openCount = board.openCount,
                pickedCount = board.pickedCount,
                completedCount = board.completedCount,
                canceledCount = board.canceledCount,
                records = board.records.map(::mapBoardRecord),
            )
        }
    }

    override fun createRestockTask(branchId: String, input: CreateRestockTaskInput): RestockTask {
        return runControlPlane {
            val task = client.createRestockTask(
                tenantId = tenantId,
                branchId = branchId,
                productId = input.productId,
                requestedQuantity = input.requestedQuantity,
                sourcePosture = input.sourcePosture,
                note = input.note,
            )
            cacheTaskMetadata(
                branchId = branchId,
                taskId = task.id,
                productName = input.productName,
                skuCode = input.skuCode,
            )
            mapTask(branchId = branchId, task = task)
        }
    }

    override fun pickRestockTask(branchId: String, taskId: String, pickedQuantity: Double, note: String?): RestockTask {
        return runControlPlane {
            val task = client.pickRestockTask(
                tenantId = tenantId,
                branchId = branchId,
                restockTaskId = taskId,
                pickedQuantity = pickedQuantity,
                note = note,
            )
            mapTask(branchId = branchId, task = task)
        }
    }

    override fun completeRestockTask(branchId: String, taskId: String, completionNote: String?): RestockTask {
        return runControlPlane {
            val task = client.completeRestockTask(
                tenantId = tenantId,
                branchId = branchId,
                restockTaskId = taskId,
                completionNote = completionNote,
            )
            mapTask(branchId = branchId, task = task)
        }
    }

    override fun cancelRestockTask(branchId: String, taskId: String, cancelNote: String?): RestockTask {
        return runControlPlane {
            val task = client.cancelRestockTask(
                tenantId = tenantId,
                branchId = branchId,
                restockTaskId = taskId,
                cancelNote = cancelNote,
            )
            mapTask(branchId = branchId, task = task)
        }
    }

    private fun mapBoardRecord(record: ControlPlaneRestockBoardRecord): RestockBoardRecord {
        return RestockBoardRecord(
            taskId = record.restockTaskId,
            taskNumber = record.taskNumber,
            productId = record.productId,
            productName = record.productName,
            skuCode = record.skuCode,
            status = record.status,
            stockOnHandSnapshot = record.stockOnHandSnapshot,
            reorderPointSnapshot = record.reorderPointSnapshot,
            targetStockSnapshot = record.targetStockSnapshot,
            suggestedQuantitySnapshot = record.suggestedQuantitySnapshot,
            requestedQuantity = record.requestedQuantity,
            pickedQuantity = record.pickedQuantity,
            sourcePosture = record.sourcePosture,
            note = record.note,
            completionNote = record.completionNote,
            activeTaskId = if (record.hasActiveTask) record.restockTaskId else null,
        )
    }

    private fun mapTask(branchId: String, task: ControlPlaneRestockTask): RestockTask {
        val metadata = requireTaskMetadata(branchId = branchId, task = task)
        return RestockTask(
            id = task.id,
            taskNumber = task.taskNumber,
            productId = task.productId,
            productName = metadata.productName,
            skuCode = metadata.skuCode,
            status = task.status,
            stockOnHandSnapshot = task.stockOnHandSnapshot,
            reorderPointSnapshot = task.reorderPointSnapshot,
            targetStockSnapshot = task.targetStockSnapshot,
            suggestedQuantitySnapshot = task.suggestedQuantitySnapshot,
            requestedQuantity = task.requestedQuantity,
            pickedQuantity = task.pickedQuantity,
            sourcePosture = task.sourcePosture,
            note = task.note,
            completionNote = task.completionNote,
        )
    }

    private fun requireTaskMetadata(branchId: String, task: ControlPlaneRestockTask): TaskMetadata {
        val cached = taskMetadataByBranch[branchId]?.get(task.id)
        if (cached != null) {
            return cached
        }
        val productRecord = requireProductRecord(branchId = branchId, productId = task.productId)
        return TaskMetadata(
            productName = productRecord.productName,
            skuCode = productRecord.skuCode,
        ).also { metadata ->
            cacheTaskMetadata(
                branchId = branchId,
                taskId = task.id,
                productName = metadata.productName,
                skuCode = metadata.skuCode,
            )
        }
    }

    private fun requireProductRecord(branchId: String, productId: String): ControlPlaneInventorySnapshotRecord {
        val existingCatalog = productCatalogByBranch[branchId]
        if (existingCatalog != null && existingCatalog.containsKey(productId)) {
            return requireNotNull(existingCatalog[productId])
        }
        val records = client.getInventorySnapshot(tenantId = tenantId, branchId = branchId).records
        productCatalogByBranch[branchId] = records.associateBy { it.productId }
        return records.firstOrNull { it.productId == productId }
            ?: throw IllegalArgumentException("Unknown restock product for branch.")
    }

    private fun cacheTaskMetadata(
        branchId: String,
        taskId: String,
        productName: String,
        skuCode: String,
    ) {
        taskMetadataByBranch.getOrPut(branchId) { mutableMapOf() }[taskId] = TaskMetadata(
            productName = productName,
            skuCode = skuCode,
        )
    }

    private fun <T> runControlPlane(action: () -> T): T {
        return try {
            action()
        } catch (error: StoreMobileControlPlaneException) {
            throw IllegalArgumentException(error.message ?: "Control-plane request failed.")
        }
    }

    private data class TaskMetadata(
        val productName: String,
        val skuCode: String,
    )
}
