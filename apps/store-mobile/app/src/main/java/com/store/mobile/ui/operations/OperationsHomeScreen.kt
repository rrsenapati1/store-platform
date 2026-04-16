package com.store.mobile.ui.operations

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

enum class MobileOperationsSection {
    SCAN,
    RESTOCK,
    RECEIVING,
    STOCK_COUNT,
    EXPIRY,
    RUNTIME,
}

@Composable
fun OperationsHomeScreen(
    activeSection: MobileOperationsSection,
    onSelectSection: (MobileOperationsSection) -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 24.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        MobileOperationsSection.entries.forEach { section ->
            Button(
                onClick = { onSelectSection(section) },
                enabled = section != activeSection,
            ) {
                Text(
                    text = mobileOperationsSectionLabel(section),
                    style = MaterialTheme.typography.labelLarge,
                )
            }
        }
    }
}
