package com.store.mobile.ui.handheld

import com.store.mobile.ui.operations.ExpiryUiState
import com.store.mobile.ui.operations.MobileOperationsSection
import com.store.mobile.ui.operations.ReceivingUiState
import com.store.mobile.ui.operations.RestockUiState
import com.store.mobile.ui.operations.StockCountUiState
import com.store.mobile.ui.scan.ScanLookupUiState

data class HandheldScanAction(
    val label: String,
    val section: MobileOperationsSection,
)

data class HandheldTaskContext(
    val title: String,
    val detail: String,
    val section: MobileOperationsSection,
)

data class HandheldQueuePreview(
    val label: String,
    val count: Int,
    val section: MobileOperationsSection,
)

data class HandheldScanActionModel(
    val primaryAction: HandheldScanAction,
    val secondaryActions: List<HandheldScanAction> = emptyList(),
    val recentTaskContexts: List<HandheldTaskContext> = emptyList(),
    val queuePreview: List<HandheldQueuePreview> = emptyList(),
)

fun buildHandheldScanActionModel(
    scanState: ScanLookupUiState,
    receivingState: ReceivingUiState,
    stockCountState: StockCountUiState,
    restockState: RestockUiState,
    expiryState: ExpiryUiState,
): HandheldScanActionModel {
    val recentTaskContexts = buildList {
        receivingState.activeDraft?.let { draft ->
            add(
                HandheldTaskContext(
                    title = "Receiving in progress",
                    detail = "${draft.purchaseOrderNumber} · ${draft.supplierName}",
                    section = MobileOperationsSection.RECEIVING,
                ),
            )
        }
        stockCountState.activeSession?.let { session ->
            add(
                HandheldTaskContext(
                    title = "Count in progress",
                    detail = "${session.productName} · ${session.status}",
                    section = MobileOperationsSection.STOCK_COUNT,
                ),
            )
        }
        restockState.activeTask?.let { task ->
            add(
                HandheldTaskContext(
                    title = "Restock in progress",
                    detail = "${task.productName} · ${task.status}",
                    section = MobileOperationsSection.RESTOCK,
                ),
            )
        }
        expiryState.activeSession?.let { session ->
            add(
                HandheldTaskContext(
                    title = "Expiry review in progress",
                    detail = "${session.productName} · ${session.status}",
                    section = MobileOperationsSection.EXPIRY,
                ),
            )
        }
    }

    val queuePreview = buildList {
        if (restockState.lowStockCount > 0) {
            add(
                HandheldQueuePreview(
                    label = "Low stock",
                    count = restockState.lowStockCount,
                    section = MobileOperationsSection.RESTOCK,
                ),
            )
        }
        val receivingReadyCount = receivingState.receivingBoard?.readyCount ?: 0
        if (receivingReadyCount > 0) {
            add(
                HandheldQueuePreview(
                    label = "Ready receipts",
                    count = receivingReadyCount,
                    section = MobileOperationsSection.RECEIVING,
                ),
            )
        }
        val countQueue = (stockCountState.board?.openCount ?: 0) + (stockCountState.board?.countedCount ?: 0)
        if (countQueue > 0) {
            add(
                HandheldQueuePreview(
                    label = "Pending counts",
                    count = countQueue,
                    section = MobileOperationsSection.STOCK_COUNT,
                ),
            )
        }
        val expiryQueue = (expiryState.report?.expiringSoonCount ?: 0) + (expiryState.report?.expiredCount ?: 0)
        if (expiryQueue > 0) {
            add(
                HandheldQueuePreview(
                    label = "Expiry risk",
                    count = expiryQueue,
                    section = MobileOperationsSection.EXPIRY,
                ),
            )
        }
    }

    val productId = scanState.productId?.takeIf { it.isNotBlank() }
    if (productId == null) {
        return HandheldScanActionModel(
            primaryAction = HandheldScanAction(
                label = "Scan another",
                section = MobileOperationsSection.SCAN,
            ),
            recentTaskContexts = recentTaskContexts,
            queuePreview = queuePreview,
        )
    }

    val actionCandidates = linkedMapOf<MobileOperationsSection, HandheldScanAction>()
    val isReceivingItem = receivingState.lineDrafts.any { it.productId == productId }
    val isLowStockItem = restockState.activeTask?.productId == productId ||
        restockState.replenishmentRecords.any { it.productId == productId } ||
        (scanState.stockOnHand != null && scanState.reorderPoint != null && scanState.stockOnHand < scanState.reorderPoint)
    val hasExpiryRisk = expiryState.activeSession?.productName == scanState.productName ||
        expiryState.report?.records?.any { it.productName == scanState.productName } == true

    if (isReceivingItem) {
        actionCandidates[MobileOperationsSection.RECEIVING] = HandheldScanAction(
            label = "Receive stock",
            section = MobileOperationsSection.RECEIVING,
        )
    }
    if (isLowStockItem) {
        actionCandidates[MobileOperationsSection.RESTOCK] = HandheldScanAction(
            label = "Restock shelf",
            section = MobileOperationsSection.RESTOCK,
        )
    }
    actionCandidates[MobileOperationsSection.STOCK_COUNT] = HandheldScanAction(
        label = "Count item",
        section = MobileOperationsSection.STOCK_COUNT,
    )
    if (hasExpiryRisk) {
        actionCandidates[MobileOperationsSection.EXPIRY] = HandheldScanAction(
            label = "Review expiry",
            section = MobileOperationsSection.EXPIRY,
        )
    }

    val orderedActions = listOf(
        actionCandidates[MobileOperationsSection.RECEIVING],
        actionCandidates[MobileOperationsSection.RESTOCK],
        actionCandidates[MobileOperationsSection.STOCK_COUNT],
        actionCandidates[MobileOperationsSection.EXPIRY],
    ).filterNotNull()

    return HandheldScanActionModel(
        primaryAction = orderedActions.firstOrNull()
            ?: HandheldScanAction(
                label = "Scan another",
                section = MobileOperationsSection.SCAN,
            ),
        secondaryActions = orderedActions.drop(1),
        recentTaskContexts = recentTaskContexts,
        queuePreview = queuePreview,
    )
}
