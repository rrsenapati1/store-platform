package com.store.mobile.controlplane

import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import org.json.JSONArray
import org.json.JSONObject

data class StoreMobileControlPlaneRequest(
    val method: String,
    val path: String,
    val authorizationHeader: String,
    val body: String? = null,
)

data class StoreMobileControlPlaneResponse(
    val statusCode: Int,
    val body: String,
)

interface StoreMobileControlPlaneTransport {
    fun execute(request: StoreMobileControlPlaneRequest): StoreMobileControlPlaneResponse
}

class JdkStoreMobileControlPlaneTransport(
    private val baseUrl: String,
) : StoreMobileControlPlaneTransport {
    override fun execute(request: StoreMobileControlPlaneRequest): StoreMobileControlPlaneResponse {
        val connection = (URL(baseUrl.trimEnd('/') + request.path).openConnection() as HttpURLConnection).apply {
            requestMethod = request.method
            setRequestProperty("Authorization", request.authorizationHeader)
            setRequestProperty("Accept", "application/json")
            if (request.body != null) {
                doOutput = true
                setRequestProperty("Content-Type", "application/json")
            }
        }
        request.body?.let { body ->
            OutputStreamWriter(connection.outputStream, Charsets.UTF_8).use { writer ->
                writer.write(body)
            }
        }
        val statusCode = connection.responseCode
        val stream = if (statusCode >= 400) connection.errorStream else connection.inputStream
        val responseBody = if (stream == null) {
            ""
        } else {
            BufferedReader(InputStreamReader(stream, Charsets.UTF_8)).use { reader ->
                reader.readText()
            }
        }
        return StoreMobileControlPlaneResponse(
            statusCode = statusCode,
            body = responseBody,
        )
    }
}

class StoreMobileControlPlaneClient(
    private val baseUrl: String,
    private val accessToken: String,
    private val transport: StoreMobileControlPlaneTransport = JdkStoreMobileControlPlaneTransport(baseUrl),
) {
    fun lookupCatalogScan(
        tenantId: String,
        branchId: String,
        barcode: String,
    ): ControlPlaneCatalogScanRecord? {
        val normalizedBarcode = barcode.trim()
        val response = transport.execute(
            StoreMobileControlPlaneRequest(
                method = "GET",
                path = "/v1/tenants/$tenantId/branches/$branchId/catalog-scan/$normalizedBarcode",
                authorizationHeader = "Bearer $accessToken",
            ),
        )
        if (response.statusCode == 404) {
            return null
        }
        if (response.statusCode >= 400) {
            throw StoreMobileControlPlaneException("Control-plane request failed (${response.statusCode}).")
        }
        val root = JSONObject(response.body)
        return ControlPlaneCatalogScanRecord(
            productId = root.getString("product_id"),
            productName = root.getString("product_name"),
            skuCode = root.getString("sku_code"),
            barcode = root.getString("barcode"),
            sellingPrice = root.getDouble("selling_price"),
            stockOnHand = root.getDouble("stock_on_hand"),
            availabilityStatus = root.getString("availability_status"),
            reorderPoint = root.optNullableDouble("reorder_point"),
            targetStock = root.optNullableDouble("target_stock"),
        )
    }

    fun getInventorySnapshot(tenantId: String, branchId: String): ControlPlaneInventorySnapshotResponse {
        val response = execute(
            method = "GET",
            path = "/v1/tenants/$tenantId/branches/$branchId/inventory-snapshot",
        )
        val root = JSONObject(response.body)
        val records = root.getJSONArray("records").mapObjects { item ->
            ControlPlaneInventorySnapshotRecord(
                productId = item.getString("product_id"),
                productName = item.getString("product_name"),
                skuCode = item.getString("sku_code"),
                stockOnHand = item.getDouble("stock_on_hand"),
                lastEntryType = item.getString("last_entry_type"),
            )
        }
        return ControlPlaneInventorySnapshotResponse(records = records)
    }

    fun getReceivingBoard(tenantId: String, branchId: String): ControlPlaneReceivingBoard {
        val response = execute(
            method = "GET",
            path = "/v1/tenants/$tenantId/branches/$branchId/receiving-board",
        )
        val root = JSONObject(response.body)
        return ControlPlaneReceivingBoard(
            branchId = root.getString("branch_id"),
            blockedCount = root.getInt("blocked_count"),
            readyCount = root.getInt("ready_count"),
            receivedCount = root.getInt("received_count"),
            receivedWithVarianceCount = root.getInt("received_with_variance_count"),
            records = root.getJSONArray("records").mapObjects { item ->
                ControlPlaneReceivingBoardRecord(
                    purchaseOrderId = item.getString("purchase_order_id"),
                    purchaseOrderNumber = item.getString("purchase_order_number"),
                    supplierName = item.getString("supplier_name"),
                    approvalStatus = item.getString("approval_status"),
                    receivingStatus = item.getString("receiving_status"),
                    canReceive = item.getBoolean("can_receive"),
                    hasDiscrepancy = item.optBoolean("has_discrepancy"),
                    varianceQuantity = if (item.isNull("variance_quantity")) 0.0 else item.getDouble("variance_quantity"),
                    blockedReason = item.optNullableString("blocked_reason"),
                    goodsReceiptId = item.optNullableString("goods_receipt_id"),
                )
            },
        )
    }

    fun getPurchaseOrder(
        tenantId: String,
        branchId: String,
        purchaseOrderId: String,
    ): ControlPlanePurchaseOrder {
        val response = execute(
            method = "GET",
            path = "/v1/tenants/$tenantId/branches/$branchId/purchase-orders/$purchaseOrderId",
        )
        val root = JSONObject(response.body)
        return ControlPlanePurchaseOrder(
            id = root.getString("id"),
            tenantId = root.getString("tenant_id"),
            branchId = root.getString("branch_id"),
            supplierId = root.getString("supplier_id"),
            purchaseOrderNumber = root.getString("purchase_order_number"),
            approvalStatus = root.getString("approval_status"),
            subtotal = root.getDouble("subtotal"),
            taxTotal = root.getDouble("tax_total"),
            grandTotal = root.getDouble("grand_total"),
            lines = root.getJSONArray("lines").mapObjects { item ->
                ControlPlanePurchaseOrderLine(
                    productId = item.getString("product_id"),
                    productName = item.getString("product_name"),
                    skuCode = item.getString("sku_code"),
                    quantity = item.getDouble("quantity"),
                    unitCost = item.getDouble("unit_cost"),
                    lineTotal = item.getDouble("line_total"),
                )
            },
        )
    }

    fun listGoodsReceipts(tenantId: String, branchId: String): ControlPlaneGoodsReceiptListResponse {
        val response = execute(
            method = "GET",
            path = "/v1/tenants/$tenantId/branches/$branchId/goods-receipts",
        )
        val root = JSONObject(response.body)
        return ControlPlaneGoodsReceiptListResponse(
            records = root.getJSONArray("records").mapObjects { item ->
                ControlPlaneGoodsReceiptRecord(
                    goodsReceiptId = item.getString("goods_receipt_id"),
                    goodsReceiptNumber = item.getString("goods_receipt_number"),
                    purchaseOrderId = item.getString("purchase_order_id"),
                    purchaseOrderNumber = item.getString("purchase_order_number"),
                    supplierId = item.getString("supplier_id"),
                    supplierName = item.getString("supplier_name"),
                    receivedOn = item.getString("received_on"),
                    lineCount = item.getInt("line_count"),
                    receivedQuantity = item.getDouble("received_quantity"),
                    orderedQuantity = item.getDouble("ordered_quantity"),
                    varianceQuantity = item.getDouble("variance_quantity"),
                    hasDiscrepancy = item.getBoolean("has_discrepancy"),
                    note = item.optNullableString("note"),
                )
            },
        )
    }

    fun createGoodsReceipt(
        tenantId: String,
        branchId: String,
        purchaseOrderId: String,
        note: String?,
        lines: List<ControlPlaneGoodsReceiptLineReceiveInput>,
    ): ControlPlaneGoodsReceipt {
        val lineJson = buildJsonArray(
            lines.map { line ->
                buildJsonObject(
                    "product_id" to "\"${escapeJson(line.productId)}\"",
                    "received_quantity" to line.receivedQuantity.toString(),
                    "discrepancy_note" to line.discrepancyNote?.takeIf { it.isNotBlank() }?.let { "\"${escapeJson(it)}\"" },
                )
            },
        )
        val body = buildJsonObject(
            "purchase_order_id" to "\"${escapeJson(purchaseOrderId)}\"",
            "note" to note?.takeIf { it.isNotBlank() }?.let { "\"${escapeJson(it)}\"" },
            "lines" to lineJson,
        )
        val response = execute(
            method = "POST",
            path = "/v1/tenants/$tenantId/branches/$branchId/goods-receipts",
            body = body,
        )
        return parseGoodsReceipt(response.body)
    }

    fun getStockCountBoard(tenantId: String, branchId: String): ControlPlaneStockCountBoard {
        val response = execute(
            method = "GET",
            path = "/v1/tenants/$tenantId/branches/$branchId/stock-count-board",
        )
        val root = JSONObject(response.body)
        return ControlPlaneStockCountBoard(
            branchId = root.getString("branch_id"),
            openCount = root.getInt("open_count"),
            countedCount = root.getInt("counted_count"),
            approvedCount = root.getInt("approved_count"),
            canceledCount = root.getInt("canceled_count"),
            records = root.getJSONArray("records").mapObjects { item ->
                ControlPlaneStockCountBoardRecord(
                    stockCountSessionId = item.getString("stock_count_session_id"),
                    sessionNumber = item.getString("session_number"),
                    productId = item.getString("product_id"),
                    productName = item.getString("product_name"),
                    skuCode = item.getString("sku_code"),
                    status = item.getString("status"),
                    expectedQuantity = item.optNullableDouble("expected_quantity"),
                    countedQuantity = item.optNullableDouble("counted_quantity"),
                    varianceQuantity = item.optNullableDouble("variance_quantity"),
                    note = item.optNullableString("note"),
                    reviewNote = item.optNullableString("review_note"),
                )
            },
        )
    }

    fun getBatchExpiryReport(tenantId: String, branchId: String): ControlPlaneBatchExpiryReport {
        val response = execute(
            method = "GET",
            path = "/v1/tenants/$tenantId/branches/$branchId/batch-expiry-report",
        )
        val root = JSONObject(response.body)
        return ControlPlaneBatchExpiryReport(
            branchId = root.getString("branch_id"),
            trackedLotCount = root.getInt("tracked_lot_count"),
            expiringSoonCount = root.getInt("expiring_soon_count"),
            expiredCount = root.getInt("expired_count"),
            untrackedStockQuantity = root.getDouble("untracked_stock_quantity"),
            records = root.getJSONArray("records").mapObjects { item ->
                ControlPlaneBatchExpiryReportRecord(
                    batchLotId = item.getString("batch_lot_id"),
                    productId = item.getString("product_id"),
                    productName = item.getString("product_name"),
                    batchNumber = item.getString("batch_number"),
                    expiryDate = item.getString("expiry_date"),
                    daysToExpiry = item.getInt("days_to_expiry"),
                    receivedQuantity = item.getDouble("received_quantity"),
                    writtenOffQuantity = item.getDouble("written_off_quantity"),
                    remainingQuantity = item.getDouble("remaining_quantity"),
                    status = item.getString("status"),
                )
            },
        )
    }

    fun getBatchExpiryBoard(tenantId: String, branchId: String): ControlPlaneBatchExpiryBoard {
        val response = execute(
            method = "GET",
            path = "/v1/tenants/$tenantId/branches/$branchId/batch-expiry-board",
        )
        val root = JSONObject(response.body)
        return ControlPlaneBatchExpiryBoard(
            branchId = root.getString("branch_id"),
            openCount = root.getInt("open_count"),
            reviewedCount = root.getInt("reviewed_count"),
            approvedCount = root.getInt("approved_count"),
            canceledCount = root.getInt("canceled_count"),
            records = root.getJSONArray("records").mapObjects { item ->
                ControlPlaneBatchExpiryBoardRecord(
                    batchExpirySessionId = item.getString("batch_expiry_session_id"),
                    sessionNumber = item.getString("session_number"),
                    batchLotId = item.getString("batch_lot_id"),
                    productId = item.getString("product_id"),
                    productName = item.getString("product_name"),
                    skuCode = item.getString("sku_code"),
                    batchNumber = item.getString("batch_number"),
                    status = item.getString("status"),
                    remainingQuantitySnapshot = item.getDouble("remaining_quantity_snapshot"),
                    proposedQuantity = item.optNullableDouble("proposed_quantity"),
                    reason = item.optNullableString("reason"),
                    note = item.optNullableString("note"),
                    reviewNote = item.optNullableString("review_note"),
                )
            },
        )
    }

    fun createBatchExpirySession(
        tenantId: String,
        branchId: String,
        batchLotId: String,
        note: String?,
    ): ControlPlaneBatchExpiryReviewSession {
        val body = buildJsonObject(
            "batch_lot_id" to "\"${escapeJson(batchLotId)}\"",
            "note" to note?.takeIf { it.isNotBlank() }?.let { "\"${escapeJson(it)}\"" },
        )
        val response = execute(
            method = "POST",
            path = "/v1/tenants/$tenantId/branches/$branchId/batch-expiry-sessions",
            body = body,
        )
        return parseBatchExpirySession(response.body)
    }

    fun recordBatchExpirySession(
        tenantId: String,
        branchId: String,
        batchExpirySessionId: String,
        quantity: Double,
        reason: String,
    ): ControlPlaneBatchExpiryReviewSession {
        val body = buildJsonObject(
            "quantity" to quantity.toString(),
            "reason" to "\"${escapeJson(reason)}\"",
        )
        val response = execute(
            method = "POST",
            path = "/v1/tenants/$tenantId/branches/$branchId/batch-expiry-sessions/$batchExpirySessionId/review",
            body = body,
        )
        return parseBatchExpirySession(response.body)
    }

    fun approveBatchExpirySession(
        tenantId: String,
        branchId: String,
        batchExpirySessionId: String,
        reviewNote: String?,
    ): ControlPlaneBatchExpiryApproval {
        val body = buildJsonObject(
            "review_note" to reviewNote?.takeIf { it.isNotBlank() }?.let { "\"${escapeJson(it)}\"" },
        )
        val response = execute(
            method = "POST",
            path = "/v1/tenants/$tenantId/branches/$branchId/batch-expiry-sessions/$batchExpirySessionId/approve",
            body = body,
        )
        val root = JSONObject(response.body)
        return ControlPlaneBatchExpiryApproval(
            session = parseBatchExpirySession(root.getJSONObject("session").toString()),
            writeOff = parseBatchExpiryWriteOff(root.getJSONObject("write_off")),
        )
    }

    fun cancelBatchExpirySession(
        tenantId: String,
        branchId: String,
        batchExpirySessionId: String,
        reviewNote: String?,
    ): ControlPlaneBatchExpiryReviewSession {
        val body = buildJsonObject(
            "review_note" to reviewNote?.takeIf { it.isNotBlank() }?.let { "\"${escapeJson(it)}\"" },
        )
        val response = execute(
            method = "POST",
            path = "/v1/tenants/$tenantId/branches/$branchId/batch-expiry-sessions/$batchExpirySessionId/cancel",
            body = body,
        )
        return parseBatchExpirySession(response.body)
    }

    fun getRestockBoard(tenantId: String, branchId: String): ControlPlaneRestockBoard {
        val response = execute(
            method = "GET",
            path = "/v1/tenants/$tenantId/branches/$branchId/restock-board",
        )
        val root = JSONObject(response.body)
        return ControlPlaneRestockBoard(
            branchId = root.getString("branch_id"),
            openCount = root.getInt("open_count"),
            pickedCount = root.getInt("picked_count"),
            completedCount = root.getInt("completed_count"),
            canceledCount = root.getInt("canceled_count"),
            records = root.getJSONArray("records").mapObjects { item ->
                ControlPlaneRestockBoardRecord(
                    restockTaskId = item.getString("restock_task_id"),
                    taskNumber = item.getString("task_number"),
                    productId = item.getString("product_id"),
                    productName = item.getString("product_name"),
                    skuCode = item.getString("sku_code"),
                    status = item.getString("status"),
                    stockOnHandSnapshot = item.getDouble("stock_on_hand_snapshot"),
                    reorderPointSnapshot = item.getDouble("reorder_point_snapshot"),
                    targetStockSnapshot = item.getDouble("target_stock_snapshot"),
                    suggestedQuantitySnapshot = item.getDouble("suggested_quantity_snapshot"),
                    requestedQuantity = item.getDouble("requested_quantity"),
                    pickedQuantity = item.optNullableDouble("picked_quantity"),
                    sourcePosture = item.getString("source_posture"),
                    note = item.optNullableString("note"),
                    completionNote = item.optNullableString("completion_note"),
                    hasActiveTask = item.getBoolean("has_active_task"),
                )
            },
        )
    }

    fun createRestockTask(
        tenantId: String,
        branchId: String,
        productId: String,
        requestedQuantity: Double,
        sourcePosture: String,
        note: String?,
    ): ControlPlaneRestockTask {
        val body = buildJsonObject(
            "product_id" to "\"${escapeJson(productId)}\"",
            "requested_quantity" to requestedQuantity.toString(),
            "source_posture" to "\"${escapeJson(sourcePosture)}\"",
            "note" to note?.takeIf { it.isNotBlank() }?.let { "\"${escapeJson(it)}\"" },
        )
        val response = execute(
            method = "POST",
            path = "/v1/tenants/$tenantId/branches/$branchId/restock-tasks",
            body = body,
        )
        return parseRestockTask(response.body)
    }

    fun pickRestockTask(
        tenantId: String,
        branchId: String,
        restockTaskId: String,
        pickedQuantity: Double,
        note: String?,
    ): ControlPlaneRestockTask {
        val body = buildJsonObject(
            "picked_quantity" to pickedQuantity.toString(),
            "note" to note?.takeIf { it.isNotBlank() }?.let { "\"${escapeJson(it)}\"" },
        )
        val response = execute(
            method = "POST",
            path = "/v1/tenants/$tenantId/branches/$branchId/restock-tasks/$restockTaskId/pick",
            body = body,
        )
        return parseRestockTask(response.body)
    }

    fun completeRestockTask(
        tenantId: String,
        branchId: String,
        restockTaskId: String,
        completionNote: String?,
    ): ControlPlaneRestockTask {
        val body = buildJsonObject(
            "completion_note" to completionNote?.takeIf { it.isNotBlank() }?.let { "\"${escapeJson(it)}\"" },
        )
        val response = execute(
            method = "POST",
            path = "/v1/tenants/$tenantId/branches/$branchId/restock-tasks/$restockTaskId/complete",
            body = body,
        )
        return parseRestockTask(response.body)
    }

    fun cancelRestockTask(
        tenantId: String,
        branchId: String,
        restockTaskId: String,
        cancelNote: String?,
    ): ControlPlaneRestockTask {
        val body = buildJsonObject(
            "cancel_note" to cancelNote?.takeIf { it.isNotBlank() }?.let { "\"${escapeJson(it)}\"" },
        )
        val response = execute(
            method = "POST",
            path = "/v1/tenants/$tenantId/branches/$branchId/restock-tasks/$restockTaskId/cancel",
            body = body,
        )
        return parseRestockTask(response.body)
    }

    fun createStockCountSession(
        tenantId: String,
        branchId: String,
        productId: String,
        note: String?,
    ): ControlPlaneStockCountReviewSession {
        val body = buildJsonObject(
            "product_id" to "\"${escapeJson(productId)}\"",
            "note" to note?.takeIf { it.isNotBlank() }?.let { "\"${escapeJson(it)}\"" },
        )
        val response = execute(
            method = "POST",
            path = "/v1/tenants/$tenantId/branches/$branchId/stock-count-sessions",
            body = body,
        )
        return parseSession(response.body)
    }

    fun recordStockCountSession(
        tenantId: String,
        branchId: String,
        stockCountSessionId: String,
        countedQuantity: Double,
        note: String?,
    ): ControlPlaneStockCountReviewSession {
        val body = buildJsonObject(
            "counted_quantity" to countedQuantity.toString(),
            "note" to note?.takeIf { it.isNotBlank() }?.let { "\"${escapeJson(it)}\"" },
        )
        val response = execute(
            method = "POST",
            path = "/v1/tenants/$tenantId/branches/$branchId/stock-count-sessions/$stockCountSessionId/record",
            body = body,
        )
        return parseSession(response.body)
    }

    fun approveStockCountSession(
        tenantId: String,
        branchId: String,
        stockCountSessionId: String,
        reviewNote: String?,
    ): ControlPlaneStockCountApproval {
        val body = buildJsonObject(
            "review_note" to reviewNote?.takeIf { it.isNotBlank() }?.let { "\"${escapeJson(it)}\"" },
        )
        val response = execute(
            method = "POST",
            path = "/v1/tenants/$tenantId/branches/$branchId/stock-count-sessions/$stockCountSessionId/approve",
            body = body,
        )
        val root = JSONObject(response.body)
        return ControlPlaneStockCountApproval(
            session = parseSession(root.getJSONObject("session").toString()),
            stockCount = parseStockCount(root.getJSONObject("stock_count")),
        )
    }

    fun cancelStockCountSession(
        tenantId: String,
        branchId: String,
        stockCountSessionId: String,
        reviewNote: String?,
    ): ControlPlaneStockCountReviewSession {
        val body = buildJsonObject(
            "review_note" to reviewNote?.takeIf { it.isNotBlank() }?.let { "\"${escapeJson(it)}\"" },
        )
        val response = execute(
            method = "POST",
            path = "/v1/tenants/$tenantId/branches/$branchId/stock-count-sessions/$stockCountSessionId/cancel",
            body = body,
        )
        return parseSession(response.body)
    }

    private fun execute(method: String, path: String, body: String? = null): StoreMobileControlPlaneResponse {
        val response = transport.execute(
            StoreMobileControlPlaneRequest(
                method = method,
                path = path,
                authorizationHeader = "Bearer $accessToken",
                body = body,
            ),
        )
        if (response.statusCode >= 400) {
            throw StoreMobileControlPlaneException("Control-plane request failed (${response.statusCode}).")
        }
        return response
    }

    private fun parseSession(raw: String): ControlPlaneStockCountReviewSession {
        val root = JSONObject(raw)
        return ControlPlaneStockCountReviewSession(
            id = root.getString("id"),
            tenantId = root.getString("tenant_id"),
            branchId = root.getString("branch_id"),
            productId = root.getString("product_id"),
            sessionNumber = root.getString("session_number"),
            status = root.getString("status"),
            expectedQuantity = root.optNullableDouble("expected_quantity"),
            countedQuantity = root.optNullableDouble("counted_quantity"),
            varianceQuantity = root.optNullableDouble("variance_quantity"),
            note = root.optNullableString("note"),
            reviewNote = root.optNullableString("review_note"),
        )
    }

    private fun parseGoodsReceipt(raw: String): ControlPlaneGoodsReceipt {
        val root = JSONObject(raw)
        return ControlPlaneGoodsReceipt(
            id = root.getString("id"),
            tenantId = root.getString("tenant_id"),
            branchId = root.getString("branch_id"),
            purchaseOrderId = root.getString("purchase_order_id"),
            supplierId = root.getString("supplier_id"),
            goodsReceiptNumber = root.getString("goods_receipt_number"),
            receivedOn = root.getString("received_on"),
            note = root.optNullableString("note"),
            orderedQuantityTotal = root.getDouble("ordered_quantity_total"),
            receivedQuantityTotal = root.getDouble("received_quantity_total"),
            varianceQuantityTotal = root.getDouble("variance_quantity_total"),
            hasDiscrepancy = root.getBoolean("has_discrepancy"),
            lines = root.getJSONArray("lines").mapObjects { item ->
                ControlPlaneGoodsReceiptLine(
                    productId = item.getString("product_id"),
                    productName = item.getString("product_name"),
                    skuCode = item.getString("sku_code"),
                    orderedQuantity = item.getDouble("ordered_quantity"),
                    quantity = item.getDouble("quantity"),
                    varianceQuantity = item.getDouble("variance_quantity"),
                    unitCost = item.getDouble("unit_cost"),
                    lineTotal = item.getDouble("line_total"),
                    discrepancyNote = item.optNullableString("discrepancy_note"),
                )
            },
        )
    }

    private fun parseStockCount(root: JSONObject): ControlPlaneStockCount {
        return ControlPlaneStockCount(
            id = root.getString("id"),
            tenantId = root.getString("tenant_id"),
            branchId = root.getString("branch_id"),
            productId = root.getString("product_id"),
            countedQuantity = root.getDouble("counted_quantity"),
            expectedQuantity = root.getDouble("expected_quantity"),
            varianceQuantity = root.getDouble("variance_quantity"),
            note = root.optNullableString("note"),
            closingStock = root.getDouble("closing_stock"),
        )
    }

    private fun parseBatchExpirySession(raw: String): ControlPlaneBatchExpiryReviewSession {
        val root = JSONObject(raw)
        return ControlPlaneBatchExpiryReviewSession(
            id = root.getString("id"),
            tenantId = root.getString("tenant_id"),
            branchId = root.getString("branch_id"),
            batchLotId = root.getString("batch_lot_id"),
            productId = root.getString("product_id"),
            sessionNumber = root.getString("session_number"),
            status = root.getString("status"),
            remainingQuantitySnapshot = root.getDouble("remaining_quantity_snapshot"),
            proposedQuantity = root.optNullableDouble("proposed_quantity"),
            reason = root.optNullableString("reason"),
            note = root.optNullableString("note"),
            reviewNote = root.optNullableString("review_note"),
        )
    }

    private fun parseBatchExpiryWriteOff(root: JSONObject): ControlPlaneBatchExpiryWriteOff {
        return ControlPlaneBatchExpiryWriteOff(
            batchLotId = root.getString("batch_lot_id"),
            productId = root.getString("product_id"),
            productName = root.getString("product_name"),
            batchNumber = root.getString("batch_number"),
            expiryDate = root.getString("expiry_date"),
            receivedQuantity = root.getDouble("received_quantity"),
            writtenOffQuantity = root.getDouble("written_off_quantity"),
            remainingQuantity = root.getDouble("remaining_quantity"),
            status = root.getString("status"),
            reason = root.getString("reason"),
        )
    }

    private fun parseRestockTask(raw: String): ControlPlaneRestockTask {
        val root = JSONObject(raw)
        return ControlPlaneRestockTask(
            id = root.getString("id"),
            tenantId = root.getString("tenant_id"),
            branchId = root.getString("branch_id"),
            productId = root.getString("product_id"),
            taskNumber = root.getString("task_number"),
            status = root.getString("status"),
            stockOnHandSnapshot = root.getDouble("stock_on_hand_snapshot"),
            reorderPointSnapshot = root.getDouble("reorder_point_snapshot"),
            targetStockSnapshot = root.getDouble("target_stock_snapshot"),
            suggestedQuantitySnapshot = root.getDouble("suggested_quantity_snapshot"),
            requestedQuantity = root.getDouble("requested_quantity"),
            pickedQuantity = root.optNullableDouble("picked_quantity"),
            sourcePosture = root.getString("source_posture"),
            note = root.optNullableString("note"),
            completionNote = root.optNullableString("completion_note"),
        )
    }
}

private fun <T> JSONArray.mapObjects(transform: (JSONObject) -> T): List<T> {
    return List(length()) { index -> transform(getJSONObject(index)) }
}

private fun JSONObject.optNullableString(key: String): String? {
    return if (isNull(key)) null else optString(key).ifBlank { null }
}

private fun JSONObject.optNullableDouble(key: String): Double? {
    return if (isNull(key)) null else getDouble(key)
}

private fun buildJsonObject(vararg fields: Pair<String, String?>): String {
    return fields
        .filter { it.second != null }
        .joinToString(separator = ",", prefix = "{", postfix = "}") { (key, value) ->
            "\"${escapeJson(key)}\":${value}"
        }
}

private fun buildJsonArray(items: List<String>): String {
    return items.joinToString(separator = ",", prefix = "[", postfix = "]")
}

private fun escapeJson(value: String): String {
    return value
        .replace("\\", "\\\\")
        .replace("\"", "\\\"")
}
