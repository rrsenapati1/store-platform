package com.store.mobile.ui.tablet

import com.store.mobile.ui.operations.ExpiryUiState
import com.store.mobile.ui.operations.ReceivingUiState
import com.store.mobile.ui.operations.RestockUiState
import com.store.mobile.ui.operations.StockCountUiState
import com.store.mobile.ui.runtime.RuntimeStatusUiState

data class InventoryTabletOverviewModel(
    val primaryDestination: InventoryTabletDestination,
    val primaryActionLabel: String,
    val runtimeBanner: String,
    val receivingSummary: String,
    val countSummary: String,
    val restockSummary: String,
    val expirySummary: String,
    val scanSummary: String,
)

fun buildInventoryTabletOverviewModel(
    receivingState: ReceivingUiState,
    stockCountState: StockCountUiState,
    restockState: RestockUiState,
    expiryState: ExpiryUiState,
    runtimeStatusState: RuntimeStatusUiState,
): InventoryTabletOverviewModel {
    val receivingReadyCount = receivingState.receivingBoard?.readyCount ?: 0
    val countOpenCount = stockCountState.board?.openCount ?: 0
    val countReviewCount = stockCountState.board?.countedCount ?: 0
    val restockSuggestedCount = restockState.lowStockCount
    val restockActiveCount = restockState.openCount + restockState.pickedCount
    val expiryOpenCount = expiryState.board?.openCount ?: 0
    val expiryReviewCount = expiryState.board?.reviewedCount ?: 0
    val expiredCount = expiryState.report?.expiredCount ?: 0

    val primaryDestination = when {
        !runtimeStatusState.connected -> InventoryTabletDestination.RUNTIME
        receivingReadyCount > 0 -> InventoryTabletDestination.RECEIVING
        countOpenCount > 0 || countReviewCount > 0 -> InventoryTabletDestination.STOCK_COUNT
        expiryOpenCount > 0 || expiryReviewCount > 0 || expiredCount > 0 -> InventoryTabletDestination.EXPIRY
        restockActiveCount > 0 || restockSuggestedCount > 0 -> InventoryTabletDestination.RESTOCK
        else -> InventoryTabletDestination.SCAN
    }
    val primaryActionLabel = when (primaryDestination) {
        InventoryTabletDestination.RUNTIME -> "Reconnect runtime"
        InventoryTabletDestination.RECEIVING -> "Review inbound receipts"
        InventoryTabletDestination.STOCK_COUNT -> "Continue stock counts"
        InventoryTabletDestination.RESTOCK -> "Coordinate shelf replenishment"
        InventoryTabletDestination.EXPIRY -> "Review expiry risks"
        InventoryTabletDestination.SCAN -> "Scan inventory"
        InventoryTabletDestination.OVERVIEW -> "Review branch overview"
    }

    return InventoryTabletOverviewModel(
        primaryDestination = primaryDestination,
        primaryActionLabel = primaryActionLabel,
        runtimeBanner = "${runtimeStatusState.title} :: ${runtimeStatusState.pendingSyncLabel}",
        receivingSummary = when {
            receivingReadyCount > 0 -> "$receivingReadyCount purchase orders ready"
            receivingState.receivingBoard?.receivedWithVarianceCount ?: 0 > 0 ->
                "${receivingState.receivingBoard?.receivedWithVarianceCount ?: 0} receipts need discrepancy follow-up"
            else -> "No inbound receipts waiting"
        },
        countSummary = when {
            countReviewCount > 0 -> "$countReviewCount blind counts waiting for review"
            countOpenCount > 0 -> "$countOpenCount counts currently open"
            else -> "${stockCountState.board?.approvedCount ?: 0} counts approved"
        },
        restockSummary = when {
            restockActiveCount > 0 -> "$restockActiveCount restock tasks in progress"
            restockSuggestedCount > 0 -> "$restockSuggestedCount shelf tasks suggested"
            else -> "${restockState.adequateCount} aisles stocked to policy"
        },
        expirySummary = when {
            expiryOpenCount + expiryReviewCount > 0 -> "${expiryOpenCount + expiryReviewCount} expiry reviews active"
            expiredCount > 0 -> "$expiredCount lots already expired"
            else -> "${expiryState.report?.expiringSoonCount ?: 0} lots expiring soon"
        },
        scanSummary = "Scan products and lots for branch lookup, replenishment, and review routing",
    )
}
