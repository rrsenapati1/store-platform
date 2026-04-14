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
import com.store.mobile.operations.ReceivingBoard

@Composable
fun ReceivingScreen(board: ReceivingBoard) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Text(text = "Receiving", style = MaterialTheme.typography.headlineSmall)
        board.records.forEach { record ->
            Text(text = record.purchaseOrderNumber, style = MaterialTheme.typography.titleMedium)
            Text(text = record.supplierName, style = MaterialTheme.typography.bodyMedium)
            Text(text = "Status: ${record.receivingStatus}", style = MaterialTheme.typography.bodyMedium)
        }
    }
}
