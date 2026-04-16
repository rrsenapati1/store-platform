package com.store.mobile.ui.operations

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

data class RestockScreenActions(
    val onRefreshBoard: () -> Unit = {},
    val onSelectReplenishmentProduct: (String) -> Unit = {},
    val onRequestedQuantityChange: (String) -> Unit = {},
    val onPickedQuantityChange: (String) -> Unit = {},
    val onNoteChange: (String) -> Unit = {},
    val onCompletionNoteChange: (String) -> Unit = {},
    val onSourcePostureChange: (String) -> Unit = {},
    val onCreateTask: () -> Unit = {},
    val onPickTask: () -> Unit = {},
    val onCompleteTask: () -> Unit = {},
    val onCancelTask: () -> Unit = {},
)

private val restockSourcePostures = listOf(
    "BACKROOM_AVAILABLE",
    "BACKROOM_UNCERTAIN",
    "BACKROOM_UNAVAILABLE",
)

@Composable
fun RestockScreen(
    state: RestockUiState,
    isTabletLayout: Boolean,
    actions: RestockScreenActions,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(text = "Assisted restock", style = MaterialTheme.typography.headlineSmall)
        Text(
            text = "Low-stock board: ${state.lowStockCount} low, ${state.adequateCount} adequate",
            style = MaterialTheme.typography.bodyMedium,
        )
        if (state.replenishmentRecords.isEmpty()) {
            Text(text = "No replenishment suggestions yet.", style = MaterialTheme.typography.bodyMedium)
        } else {
            state.replenishmentRecords.forEach { record ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    OutlinedButton(
                        onClick = { actions.onSelectReplenishmentProduct(record.productId) },
                    ) {
                        Text(text = "Select ${record.productName}")
                    }
                    Text(
                        text = "${record.replenishmentStatus} :: suggested ${record.suggestedReorderQuantity}",
                        style = MaterialTheme.typography.bodyMedium,
                        modifier = Modifier.padding(top = 12.dp),
                    )
                }
            }
        }

        if (state.productId == null) {
            Text(
                text = "Select a low-stock item from the replenishment board or scan and look up a branch item first, then use this screen to raise and progress a shelf/backroom restock task.",
                style = MaterialTheme.typography.bodyMedium,
            )
        } else {
            Text(text = state.productName, style = MaterialTheme.typography.titleMedium)
            Text(text = "SKU: ${state.skuCode}", style = MaterialTheme.typography.bodyMedium)
            Text(text = "Stock on hand: ${state.stockOnHand ?: 0}", style = MaterialTheme.typography.bodyMedium)
            Text(
                text = if (state.reorderPoint != null && state.targetStock != null) {
                    "Policy: reorder ${state.reorderPoint}, target ${state.targetStock}, suggested ${state.suggestedQuantity ?: 0}"
                } else {
                    "This scanned product does not have a branch replenishment policy yet."
                },
                style = MaterialTheme.typography.bodyMedium,
            )
            if (state.activeTask != null) {
                Text(
                    text = "Active task: ${state.activeTask.taskNumber} (${state.activeTask.status})",
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }

        if (state.errorMessage != null) {
            Text(
                text = state.errorMessage,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.error,
            )
        }

        OutlinedTextField(
            value = state.requestedQuantity,
            onValueChange = actions.onRequestedQuantityChange,
            label = { Text("Requested quantity") },
            modifier = Modifier.fillMaxWidth(),
            enabled = state.productId != null,
        )
        OutlinedTextField(
            value = state.pickedQuantity,
            onValueChange = actions.onPickedQuantityChange,
            label = { Text("Picked quantity") },
            modifier = Modifier.fillMaxWidth(),
            enabled = state.productId != null,
        )
        OutlinedTextField(
            value = state.note,
            onValueChange = actions.onNoteChange,
            label = { Text("Restock note") },
            modifier = Modifier.fillMaxWidth(),
            enabled = state.productId != null,
        )
        OutlinedTextField(
            value = state.completionNote,
            onValueChange = actions.onCompletionNoteChange,
            label = { Text("Completion note") },
            modifier = Modifier.fillMaxWidth(),
            enabled = state.productId != null,
        )

        Text(text = "Source posture", style = MaterialTheme.typography.titleSmall)
        if (isTabletLayout) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                restockSourcePostures.forEach { posture ->
                    SourcePostureButton(
                        posture = posture,
                        selected = posture == state.sourcePosture,
                        onSelect = { actions.onSourcePostureChange(posture) },
                    )
                }
            }
        } else {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                restockSourcePostures.forEach { posture ->
                    SourcePostureButton(
                        posture = posture,
                        selected = posture == state.sourcePosture,
                        onSelect = { actions.onSourcePostureChange(posture) },
                    )
                }
            }
        }

        if (isTabletLayout) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                RestockActionButtons(state = state, actions = actions)
            }
        } else {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                RestockActionButtons(state = state, actions = actions)
            }
        }

        Text(
            text = "Board: open ${state.openCount}, picked ${state.pickedCount}, completed ${state.completedCount}, canceled ${state.canceledCount}",
            style = MaterialTheme.typography.bodyMedium,
        )
        if (state.records.isEmpty()) {
            Text(text = "No restock tasks recorded yet.", style = MaterialTheme.typography.bodyMedium)
        } else {
            state.records.forEach { record ->
                Text(
                    text = buildString {
                        append(record.taskNumber)
                        append(" :: ")
                        append(record.productName)
                        append(" :: ")
                        append(record.status)
                        append(" :: requested ")
                        append(record.requestedQuantity)
                        if (record.pickedQuantity != null) {
                            append(" :: picked ")
                            append(record.pickedQuantity)
                        }
                        if (!record.completionNote.isNullOrBlank()) {
                            append(" :: ")
                            append(record.completionNote)
                        } else if (!record.note.isNullOrBlank()) {
                            append(" :: ")
                            append(record.note)
                        }
                    },
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
    }
}

@Composable
private fun SourcePostureButton(
    posture: String,
    selected: Boolean,
    onSelect: () -> Unit,
) {
    if (selected) {
        Button(onClick = onSelect) {
            Text(text = postureLabel(posture))
        }
    } else {
        OutlinedButton(onClick = onSelect) {
            Text(text = postureLabel(posture))
        }
    }
}

@Composable
private fun RestockActionButtons(
    state: RestockUiState,
    actions: RestockScreenActions,
) {
    val modifier = Modifier.fillMaxWidth()
    OutlinedButton(
        onClick = actions.onRefreshBoard,
        modifier = modifier,
    ) {
        Text(text = "Refresh board")
    }
    Button(
        onClick = actions.onCreateTask,
        modifier = modifier,
        enabled = state.productId != null && state.requestedQuantity.isNotBlank(),
    ) {
        Text(text = "Create task")
    }
    Button(
        onClick = actions.onPickTask,
        modifier = modifier,
        enabled = state.activeTask != null && state.pickedQuantity.isNotBlank(),
    ) {
        Text(text = "Mark picked")
    }
    Button(
        onClick = actions.onCompleteTask,
        modifier = modifier,
        enabled = state.activeTask?.status == "PICKED",
    ) {
        Text(text = "Complete")
    }
    OutlinedButton(
        onClick = actions.onCancelTask,
        modifier = modifier,
        enabled = state.activeTask != null,
    ) {
        Text(text = "Cancel")
    }
}

private fun postureLabel(posture: String): String {
    return when (posture) {
        "BACKROOM_AVAILABLE" -> "Backroom available"
        "BACKROOM_UNCERTAIN" -> "Backroom uncertain"
        "BACKROOM_UNAVAILABLE" -> "Backroom unavailable"
        else -> posture
    }
}
