package com.store.mobile.ui.tablet

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
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
fun InventoryTabletSectionRail(
    activeDestination: InventoryTabletDestination,
    onSelectDestination: (InventoryTabletDestination) -> Unit,
) {
    Card(
        modifier = Modifier
            .fillMaxHeight()
            .fillMaxWidth(),
    ) {
        Column(
            modifier = Modifier
                .fillMaxHeight()
                .fillMaxWidth()
                .padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text(text = "Inventory tablet", style = MaterialTheme.typography.headlineSmall)
            Text(
                text = "Backroom-first branch runtime for receipts, counts, replenishment, scan, and runtime posture.",
                style = MaterialTheme.typography.bodyMedium,
            )
            InventoryTabletDestination.entries.forEach { destination ->
                if (destination == activeDestination) {
                    Button(
                        onClick = { onSelectDestination(destination) },
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text(text = inventoryTabletDestinationLabel(destination))
                    }
                } else {
                    OutlinedButton(
                        onClick = { onSelectDestination(destination) },
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text(text = inventoryTabletDestinationLabel(destination))
                    }
                }
            }
        }
    }
}

fun inventoryTabletDestinationLabel(destination: InventoryTabletDestination): String {
    return when (destination) {
        InventoryTabletDestination.OVERVIEW -> "Overview"
        InventoryTabletDestination.RECEIVING -> "Receiving"
        InventoryTabletDestination.STOCK_COUNT -> "Count"
        InventoryTabletDestination.RESTOCK -> "Restock"
        InventoryTabletDestination.EXPIRY -> "Expiry"
        InventoryTabletDestination.SCAN -> "Scan"
        InventoryTabletDestination.RUNTIME -> "Runtime"
    }
}
