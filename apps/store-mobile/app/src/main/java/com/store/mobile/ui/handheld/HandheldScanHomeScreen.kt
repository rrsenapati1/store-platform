package com.store.mobile.ui.handheld

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.unit.dp
import com.store.mobile.ui.operations.MobileOperationsSection
import com.store.mobile.ui.scan.ScanLookupDetailsPanel
import com.store.mobile.ui.scan.ScanLookupUiState

@Composable
fun HandheldScanHomeScreen(
    state: ScanLookupUiState,
    focusRequester: FocusRequester,
    actionModel: HandheldScanActionModel,
    onDraftBarcodeChange: (String) -> Unit,
    onLookupBarcode: () -> Unit,
    onConfigureZebraDataWedge: () -> Unit,
    onSelectTaskSection: (MobileOperationsSection) -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(18.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp),
            ) {
                Text(
                    text = "Scan",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary,
                )
                Text(
                    text = "Point the camera or scanner at an item and move directly into the next task.",
                    style = MaterialTheme.typography.titleMedium,
                )
                Text(
                    text = when {
                        state.productName.isNotBlank() -> "Last scanned: ${state.productName}"
                        else -> "No item scanned yet."
                    },
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        ScanLookupDetailsPanel(
            modifier = Modifier.fillMaxWidth(),
            state = state,
            focusRequester = focusRequester,
            onDraftBarcodeChange = onDraftBarcodeChange,
            onLookupBarcode = onLookupBarcode,
            onConfigureZebraDataWedge = onConfigureZebraDataWedge,
        )

        Card(modifier = Modifier.fillMaxWidth()) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(18.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Text(
                    text = "Recommended next action",
                    style = MaterialTheme.typography.titleMedium,
                )
                Button(
                    onClick = { onSelectTaskSection(actionModel.primaryAction.section) },
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text(actionModel.primaryAction.label)
                }
                if (actionModel.secondaryActions.isNotEmpty()) {
                    Column(
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        actionModel.secondaryActions.forEach { action ->
                            OutlinedButton(
                                onClick = { onSelectTaskSection(action.section) },
                                modifier = Modifier.fillMaxWidth(),
                            ) {
                                Text(action.label)
                            }
                        }
                    }
                }
            }
        }

        if (actionModel.recentTaskContexts.isNotEmpty()) {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(18.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Text(
                        text = "Resume work",
                        style = MaterialTheme.typography.titleMedium,
                    )
                    actionModel.recentTaskContexts.forEach { task ->
                        OutlinedButton(
                            onClick = { onSelectTaskSection(task.section) },
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Column(
                                modifier = Modifier.fillMaxWidth(),
                                verticalArrangement = Arrangement.spacedBy(2.dp),
                            ) {
                                Text(task.title)
                                Text(
                                    text = task.detail,
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                )
                            }
                        }
                    }
                }
            }
        }

        if (actionModel.queuePreview.isNotEmpty()) {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(18.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Text(
                        text = "Task queue",
                        style = MaterialTheme.typography.titleMedium,
                    )
                    actionModel.queuePreview.forEach { queue ->
                        OutlinedButton(
                            onClick = { onSelectTaskSection(queue.section) },
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Text("${queue.label} · ${queue.count}")
                        }
                    }
                }
            }
        }
    }
}
