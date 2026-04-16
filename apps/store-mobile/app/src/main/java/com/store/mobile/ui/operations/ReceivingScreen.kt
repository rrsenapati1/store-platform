package com.store.mobile.ui.operations

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

data class ReceivingScreenActions(
    val onLineReceivedQuantityChange: (String, String) -> Unit = { _, _ -> },
    val onLineDiscrepancyNoteChange: (String, String) -> Unit = { _, _ -> },
    val onReceiptNoteChange: (String) -> Unit = {},
    val onSubmitReviewedReceipt: () -> Unit = {},
)

@Composable
fun ReceivingScreen(
    state: ReceivingUiState,
    actions: ReceivingScreenActions,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Text(text = "Receiving", style = MaterialTheme.typography.headlineSmall)

        val boardRecord = state.receivingBoard?.records?.firstOrNull()
        if (state.activeDraft != null) {
            Text(text = state.activeDraft.purchaseOrderNumber, style = MaterialTheme.typography.titleMedium)
            Text(text = state.activeDraft.supplierName, style = MaterialTheme.typography.bodyMedium)
            Text(
                text = "Status: ${boardRecord?.receivingStatus ?: "READY"}",
                style = MaterialTheme.typography.bodyMedium,
            )
        } else {
            Text(
                text = "No approved purchase order is waiting for reviewed receipt on this branch.",
                style = MaterialTheme.typography.bodyMedium,
            )
        }

        if (state.errorMessage != null) {
            Text(
                text = state.errorMessage,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.error,
            )
        }

        state.lineDrafts.forEach { line ->
            Text(text = line.productName, style = MaterialTheme.typography.titleMedium)
            Text(
                text = "${line.skuCode} :: ordered ${line.orderedQuantity}",
                style = MaterialTheme.typography.bodyMedium,
            )
            OutlinedTextField(
                value = line.receivedQuantity,
                onValueChange = { actions.onLineReceivedQuantityChange(line.productId, it) },
                label = { Text("Received quantity") },
                modifier = Modifier.fillMaxWidth(),
                enabled = boardRecord?.canReceive != false,
            )
            OutlinedTextField(
                value = line.discrepancyNote,
                onValueChange = { actions.onLineDiscrepancyNoteChange(line.productId, it) },
                label = { Text("Discrepancy note") },
                modifier = Modifier.fillMaxWidth(),
                enabled = boardRecord?.canReceive != false,
            )
        }

        OutlinedTextField(
            value = state.receiptNote,
            onValueChange = actions.onReceiptNoteChange,
            label = { Text("Receipt note") },
            modifier = Modifier.fillMaxWidth(),
            enabled = boardRecord?.canReceive != false,
        )

        Text(
            text = "Ordered ${state.receiptSummary.orderedQuantity} :: received ${state.receiptSummary.receivedQuantity} :: variance ${state.receiptSummary.varianceQuantity}",
            style = MaterialTheme.typography.bodyMedium,
        )

        Button(
            onClick = actions.onSubmitReviewedReceipt,
            enabled = state.activeDraft != null && boardRecord?.canReceive != false,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text(text = "Create reviewed goods receipt")
        }

        if (state.latestGoodsReceipt != null) {
            Text(text = "Latest goods receipt", style = MaterialTheme.typography.titleMedium)
            Text(
                text = "${state.latestGoodsReceipt.goodsReceiptNumber} :: received ${state.latestGoodsReceipt.receivedQuantityTotal.toInt()} :: variance ${state.latestGoodsReceipt.varianceQuantityTotal.toInt()}",
                style = MaterialTheme.typography.bodyMedium,
            )
            if (!state.latestGoodsReceipt.note.isNullOrBlank()) {
                Text(text = state.latestGoodsReceipt.note, style = MaterialTheme.typography.bodyMedium)
            }
            state.latestGoodsReceipt.lines.forEach { line ->
                Text(
                    text = buildString {
                        append(line.productName)
                        append(" :: received ")
                        append(line.quantity.toInt())
                        append(" / ordered ")
                        append(line.orderedQuantity.toInt())
                        append(" :: variance ")
                        append(line.varianceQuantity.toInt())
                        if (!line.discrepancyNote.isNullOrBlank()) {
                            append(" :: ")
                            append(line.discrepancyNote)
                        }
                    },
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }

        if (state.receivingBoard != null) {
            Text(
                text = "Board: ready ${state.receivingBoard.readyCount}, received ${state.receivingBoard.receivedCount}, received with variance ${state.receivingBoard.receivedWithVarianceCount}",
                style = MaterialTheme.typography.bodyMedium,
            )
        }
    }
}
