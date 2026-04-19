package com.store.mobile.ui.handheld

import com.store.mobile.ui.operations.ExpiryUiState
import com.store.mobile.ui.operations.ReceivingUiState
import com.store.mobile.ui.operations.RestockUiState
import com.store.mobile.ui.operations.StockCountUiState
import com.store.mobile.ui.scan.ScanCameraStatus
import com.store.mobile.ui.scan.ScanLookupUiState

data class HandheldScanHeroModel(
    val eyebrow: String,
    val title: String,
    val detail: String,
    val primaryActionLabel: String,
)

data class HandheldTaskPostureModel(
    val eyebrow: String,
    val title: String,
    val detail: String,
)

fun buildHandheldScanHeroModel(
    state: ScanLookupUiState,
    actionModel: HandheldScanActionModel,
): HandheldScanHeroModel {
    return when {
        state.errorMessage != null -> HandheldScanHeroModel(
            eyebrow = "Needs attention",
            title = "Lookup needs attention",
            detail = state.errorMessage,
            primaryActionLabel = actionModel.primaryAction.label,
        )

        state.productName.isNotBlank() -> HandheldScanHeroModel(
            eyebrow = "Scanned item",
            title = state.productName,
            detail = buildString {
                append("Barcode ${state.barcode.ifBlank { state.draftBarcode.ifBlank { "pending" } }}")
                if (state.stockLabel.isNotBlank()) {
                    append(" · Stock ${state.stockLabel}")
                }
                if (state.availabilityStatus.isNotBlank()) {
                    append(" · ${state.availabilityStatus}")
                }
            },
            primaryActionLabel = actionModel.primaryAction.label,
        )

        state.cameraStatus == ScanCameraStatus.CHECKING -> HandheldScanHeroModel(
            eyebrow = "Scan ready",
            title = "Scanner warming up",
            detail = "Preparing camera and rugged-scanner inputs for the next lookup so the handheld can route straight into the right task.",
            primaryActionLabel = actionModel.primaryAction.label,
        )

        state.cameraStatus == ScanCameraStatus.PERMISSION_REQUIRED -> HandheldScanHeroModel(
            eyebrow = "Scan ready",
            title = "Allow camera scanning",
            detail = "Camera access is still blocked. You can grant permission now or continue with rugged-scanner and manual barcode fallback.",
            primaryActionLabel = actionModel.primaryAction.label,
        )

        state.cameraStatus == ScanCameraStatus.UNAVAILABLE -> HandheldScanHeroModel(
            eyebrow = "Fallback active",
            title = "Use scanner or manual barcode",
            detail = state.cameraMessage
                ?: "The live camera preview is unavailable, so the handheld should fall back to rugged-scanner broadcasts or manual barcode entry.",
            primaryActionLabel = actionModel.primaryAction.label,
        )

        else -> HandheldScanHeroModel(
            eyebrow = "Scan ready",
            title = "Ready for the next scan",
            detail = "Use camera, rugged scanner, or manual barcode entry to identify the next item and jump directly into the right task flow.",
            primaryActionLabel = actionModel.primaryAction.label,
        )
    }
}

fun buildHandheldTaskPostureModel(
    receivingState: ReceivingUiState,
    stockCountState: StockCountUiState,
    restockState: RestockUiState,
    expiryState: ExpiryUiState,
): HandheldTaskPostureModel {
    val activeLabels = buildList {
        if (receivingState.activeDraft != null) add("Receiving")
        if (stockCountState.activeSession != null) add("Count")
        if (restockState.activeTask != null) add("Restock")
        if (expiryState.activeSession != null) add("Expiry")
    }
    if (activeLabels.isNotEmpty()) {
        return HandheldTaskPostureModel(
            eyebrow = "Resume work",
            title = "${activeLabels.size} active tasks underway",
            detail = "${activeLabels.joinToString(", ")} work is already in progress on this device. Reopen the right task and keep moving instead of starting from a blank screen.",
        )
    }

    val queueLabels = buildList {
        val receivingReadyCount = receivingState.receivingBoard?.readyCount ?: 0
        if (receivingReadyCount > 0) add("$receivingReadyCount receipts ready")

        val countQueue = (stockCountState.board?.openCount ?: 0) + (stockCountState.board?.countedCount ?: 0)
        if (countQueue > 0) add("$countQueue counts waiting")

        val restockQueue = restockState.lowStockCount + restockState.openCount + restockState.pickedCount
        if (restockQueue > 0) add("$restockQueue restock tasks waiting")

        val expiryQueue = (expiryState.board?.openCount ?: 0) +
            (expiryState.board?.reviewedCount ?: 0) +
            (expiryState.report?.expiredCount ?: 0)
        if (expiryQueue > 0) add("$expiryQueue expiry reviews waiting")
    }
    if (queueLabels.isNotEmpty()) {
        return HandheldTaskPostureModel(
            eyebrow = "Queue overview",
            title = "${queueLabels.size} task queues waiting",
            detail = queueLabels.joinToString(" · "),
        )
    }

    return HandheldTaskPostureModel(
        eyebrow = "Task queues clear",
        title = "No active task queues",
        detail = "Use Scan to identify the next receiving, count, restock, or expiry action, then jump into the relevant task without digging through empty boards.",
    )
}
