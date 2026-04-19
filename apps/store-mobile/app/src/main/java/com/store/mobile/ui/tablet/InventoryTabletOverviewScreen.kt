package com.store.mobile.ui.tablet

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun InventoryTabletOverviewScreen(
    model: InventoryTabletOverviewModel,
    onSelectDestination: (InventoryTabletDestination) -> Unit,
) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(24.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Text(
                    text = "Branch inventory overview",
                    style = MaterialTheme.typography.headlineSmall,
                )
                Text(
                    text = model.runtimeBanner,
                    style = MaterialTheme.typography.bodyMedium,
                )
                Button(onClick = { onSelectDestination(model.primaryDestination) }) {
                    Text(text = model.primaryActionLabel)
                }
            }
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            OverviewSummaryCard(
                modifier = Modifier.weight(1f),
                title = "Receiving",
                detail = model.receivingSummary,
                actionLabel = "Open receiving",
                onAction = { onSelectDestination(InventoryTabletDestination.RECEIVING) },
            )
            OverviewSummaryCard(
                modifier = Modifier.weight(1f),
                title = "Stock count",
                detail = model.countSummary,
                actionLabel = "Open count",
                onAction = { onSelectDestination(InventoryTabletDestination.STOCK_COUNT) },
            )
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            OverviewSummaryCard(
                modifier = Modifier.weight(1f),
                title = "Restock",
                detail = model.restockSummary,
                actionLabel = "Open restock",
                onAction = { onSelectDestination(InventoryTabletDestination.RESTOCK) },
            )
            OverviewSummaryCard(
                modifier = Modifier.weight(1f),
                title = "Expiry",
                detail = model.expirySummary,
                actionLabel = "Open expiry",
                onAction = { onSelectDestination(InventoryTabletDestination.EXPIRY) },
            )
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            OverviewSummaryCard(
                modifier = Modifier.weight(1f),
                title = "Scan desk",
                detail = model.scanSummary,
                actionLabel = "Open scan",
                onAction = { onSelectDestination(InventoryTabletDestination.SCAN) },
            )
            OverviewSummaryCard(
                modifier = Modifier.weight(1f),
                title = "Runtime",
                detail = model.runtimeBanner,
                actionLabel = "Open runtime",
                onAction = { onSelectDestination(InventoryTabletDestination.RUNTIME) },
            )
        }
    }
}

@Composable
private fun OverviewSummaryCard(
    modifier: Modifier = Modifier,
    title: String,
    detail: String,
    actionLabel: String,
    onAction: () -> Unit,
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .heightIn(min = 156.dp),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text(text = title, style = MaterialTheme.typography.titleMedium)
            Text(text = detail, style = MaterialTheme.typography.bodyMedium)
            OutlinedButton(onClick = onAction) {
                Text(text = actionLabel)
            }
        }
    }
}
