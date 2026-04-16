package com.store.mobile.ui.operations

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
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

data class StockCountScreenActions(
    val onCreateSession: (String, String?) -> Unit = { _, _ -> },
    val onBlindCountQuantityChange: (String) -> Unit = {},
    val onBlindCountNoteChange: (String) -> Unit = {},
    val onReviewNoteChange: (String) -> Unit = {},
    val onRecordBlindCount: () -> Unit = {},
    val onApproveSession: () -> Unit = {},
    val onCancelSession: () -> Unit = {},
)

@Composable
fun StockCountScreen(
    state: StockCountUiState,
    actions: StockCountScreenActions,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Text(text = "Stock count", style = MaterialTheme.typography.headlineSmall)

        val firstRecord = state.context?.records?.firstOrNull()
        if (firstRecord != null) {
            Text(text = firstRecord.productName, style = MaterialTheme.typography.titleMedium)
            Text(text = "SKU: ${firstRecord.skuCode}", style = MaterialTheme.typography.bodyMedium)
            if (state.activeSession?.status == "COUNTED" || state.activeSession?.status == "APPROVED") {
                Text(text = "Expected: ${firstRecord.expectedQuantity.toInt()}", style = MaterialTheme.typography.bodyMedium)
            } else {
                Text(text = "Expected quantity stays hidden until the blind count is recorded.", style = MaterialTheme.typography.bodyMedium)
            }
        }

        if (state.errorMessage != null) {
            Text(
                text = state.errorMessage,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.error,
            )
        }

        if (state.activeSession == null && firstRecord != null) {
            Button(
                onClick = { actions.onCreateSession(firstRecord.productId, "Blind count before aisle reset") },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(text = "Open stock-count session")
            }
        }

        if (state.activeSession != null) {
            Text(
                text = "Active session: ${state.activeSession.sessionNumber} (${state.activeSession.status})",
                style = MaterialTheme.typography.bodyMedium,
            )
            OutlinedTextField(
                value = state.blindCountQuantity,
                onValueChange = actions.onBlindCountQuantityChange,
                label = { Text("Blind counted quantity") },
                modifier = Modifier.fillMaxWidth(),
                enabled = state.activeSession.status == "OPEN",
            )
            OutlinedTextField(
                value = state.blindCountNote,
                onValueChange = actions.onBlindCountNoteChange,
                label = { Text("Count note") },
                modifier = Modifier.fillMaxWidth(),
                enabled = state.activeSession.status == "OPEN" || state.activeSession.status == "COUNTED",
            )
            if (state.activeSession.status == "COUNTED") {
                Text(
                    text = "Variance: ${state.activeSession.varianceQuantity?.toInt() ?: 0}",
                    style = MaterialTheme.typography.bodyMedium,
                )
                OutlinedTextField(
                    value = state.reviewNote,
                    onValueChange = actions.onReviewNoteChange,
                    label = { Text("Review note") },
                    modifier = Modifier.fillMaxWidth(),
                )
            }

            if (state.activeSession.status == "OPEN") {
                Button(
                    onClick = actions.onRecordBlindCount,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(text = "Record blind count")
                }
            }

            if (state.activeSession.status == "COUNTED") {
                Button(
                    onClick = actions.onApproveSession,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(text = "Approve stock count")
                }
            }

            OutlinedButton(
                onClick = actions.onCancelSession,
                modifier = Modifier.fillMaxWidth(),
                enabled = state.activeSession.status == "OPEN" || state.activeSession.status == "COUNTED",
            ) {
                Text(text = "Cancel stock count session")
            }
        }

        if (state.latestApprovedCount != null) {
            Text(text = "Latest approved count", style = MaterialTheme.typography.titleMedium)
            Text(
                text = "${state.latestApprovedCount.session.sessionNumber} :: variance ${state.latestApprovedCount.stockCount.varianceQuantity.toInt()} :: closing stock ${state.latestApprovedCount.stockCount.closingStock.toInt()}",
                style = MaterialTheme.typography.bodyMedium,
            )
        }

        if (state.board != null) {
            Text(
                text = "Board: open ${state.board.openCount}, counted ${state.board.countedCount}, approved ${state.board.approvedCount}, canceled ${state.board.canceledCount}",
                style = MaterialTheme.typography.bodyMedium,
            )
        }
    }
}
