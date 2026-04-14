package com.store.mobile.ui.operations

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.store.mobile.operations.ExpiryReport

@Composable
fun ExpiryScreen(report: ExpiryReport) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Text(text = "Expiry", style = MaterialTheme.typography.headlineSmall)
        report.records.forEach { record ->
            Text(text = record.batchNumber, style = MaterialTheme.typography.titleMedium)
            Text(text = record.productName, style = MaterialTheme.typography.bodyMedium)
            Text(text = "Expiry: ${record.expiryDate}", style = MaterialTheme.typography.bodyMedium)
            Text(text = "Status: ${record.status}", style = MaterialTheme.typography.bodyMedium)
        }
    }
}
