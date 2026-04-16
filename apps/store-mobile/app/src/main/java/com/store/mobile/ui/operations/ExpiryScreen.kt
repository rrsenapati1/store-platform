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

data class ExpiryScreenActions(
    val onCreateSession: (String, String?) -> Unit = { _, _ -> },
    val onProposedQuantityChange: (String) -> Unit = {},
    val onWriteOffReasonChange: (String) -> Unit = {},
    val onSessionNoteChange: (String) -> Unit = {},
    val onReviewNoteChange: (String) -> Unit = {},
    val onRecordReview: () -> Unit = {},
    val onApproveSession: () -> Unit = {},
    val onCancelSession: () -> Unit = {},
)

@Composable
fun ExpiryScreen(
    state: ExpiryUiState,
    actions: ExpiryScreenActions,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Text(text = "Expiry", style = MaterialTheme.typography.headlineSmall)

        val firstRecord = state.report?.records?.firstOrNull()
        if (firstRecord != null) {
            Text(text = firstRecord.batchNumber, style = MaterialTheme.typography.titleMedium)
            Text(text = firstRecord.productName, style = MaterialTheme.typography.bodyMedium)
            Text(text = "Expiry: ${firstRecord.expiryDate}", style = MaterialTheme.typography.bodyMedium)
            Text(
                text = "Remaining ${firstRecord.remainingQuantity.toInt()} :: ${firstRecord.status}",
                style = MaterialTheme.typography.bodyMedium,
            )
        } else {
            Text(
                text = "No expiring lots are currently available for review on this branch.",
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

        if (state.activeSession == null && firstRecord != null) {
            Button(
                onClick = { actions.onCreateSession(firstRecord.batchLotId, "Shelf review before write-off") },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(text = "Open expiry review session")
            }
        }

        if (state.activeSession != null) {
            Text(
                text = "Active session: ${state.activeSession.sessionNumber} (${state.activeSession.status})",
                style = MaterialTheme.typography.bodyMedium,
            )
            Text(
                text = "Snapshot remaining quantity: ${state.activeSession.remainingQuantitySnapshot.toInt()}",
                style = MaterialTheme.typography.bodyMedium,
            )

            OutlinedTextField(
                value = state.proposedQuantity,
                onValueChange = actions.onProposedQuantityChange,
                label = { Text("Proposed write-off quantity") },
                modifier = Modifier.fillMaxWidth(),
                enabled = state.activeSession.status == "OPEN",
            )
            OutlinedTextField(
                value = state.writeOffReason,
                onValueChange = actions.onWriteOffReasonChange,
                label = { Text("Expiry write-off reason") },
                modifier = Modifier.fillMaxWidth(),
                enabled = state.activeSession.status == "OPEN",
            )
            OutlinedTextField(
                value = state.sessionNote,
                onValueChange = actions.onSessionNoteChange,
                label = { Text("Expiry session note") },
                modifier = Modifier.fillMaxWidth(),
                enabled = state.activeSession.status == "OPEN",
            )

            if (state.activeSession.status == "OPEN") {
                Button(
                    onClick = actions.onRecordReview,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(text = "Record expiry review")
                }
            }

            if (state.activeSession.status == "REVIEWED") {
                Text(
                    text = "Proposed ${state.activeSession.proposedQuantity?.toInt() ?: 0} :: ${state.activeSession.reason.orEmpty()}",
                    style = MaterialTheme.typography.bodyMedium,
                )
                OutlinedTextField(
                    value = state.reviewNote,
                    onValueChange = actions.onReviewNoteChange,
                    label = { Text("Expiry review note") },
                    modifier = Modifier.fillMaxWidth(),
                )
                Button(
                    onClick = actions.onApproveSession,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(text = "Approve expiry session")
                }
            }

            OutlinedButton(
                onClick = actions.onCancelSession,
                modifier = Modifier.fillMaxWidth(),
                enabled = state.activeSession.status == "OPEN" || state.activeSession.status == "REVIEWED",
            ) {
                Text(text = "Cancel expiry session")
            }
        }

        if (state.latestApprovedWriteOff != null) {
            Text(text = "Latest expiry write-off", style = MaterialTheme.typography.titleMedium)
            Text(
                text = "${state.latestApprovedWriteOff.session.sessionNumber} :: wrote off ${state.latestApprovedWriteOff.writeOff.writeOffQuantity.toInt()} :: remaining ${state.latestApprovedWriteOff.writeOff.remainingQuantityAfterWriteOff.toInt()}",
                style = MaterialTheme.typography.bodyMedium,
            )
        }

        if (state.report != null) {
            Text(
                text = "Report: tracked ${state.report.trackedLotCount}, expiring soon ${state.report.expiringSoonCount}, expired ${state.report.expiredCount}",
                style = MaterialTheme.typography.bodyMedium,
            )
        }

        if (state.board != null) {
            Text(
                text = "Board: open ${state.board.openCount}, reviewed ${state.board.reviewedCount}, approved ${state.board.approvedCount}, canceled ${state.board.canceledCount}",
                style = MaterialTheme.typography.bodyMedium,
            )
        }
    }
}
