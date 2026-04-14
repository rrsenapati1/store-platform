package com.store.mobile.ui.scan

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

@Composable
fun ScanLookupScreen(
    draftBarcode: String,
    state: ScanLookupUiState,
    onDraftBarcodeChange: (String) -> Unit,
    onLookupBarcode: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text(
            text = "Scan and lookup",
            style = MaterialTheme.typography.headlineSmall,
        )
        Text(
            text = "Camera permission is declared; the first slice uses the same barcode path through manual entry until live preview wiring lands.",
            style = MaterialTheme.typography.bodyMedium,
        )
        OutlinedTextField(
            value = draftBarcode,
            onValueChange = onDraftBarcodeChange,
            label = { Text("Barcode") },
            modifier = Modifier.fillMaxWidth(),
            singleLine = true,
        )
        Button(
            onClick = onLookupBarcode,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Lookup barcode")
        }
        if (state.productName.isNotBlank()) {
            Text(text = state.productName, style = MaterialTheme.typography.titleLarge)
            Text(text = "Barcode: ${state.barcode}", style = MaterialTheme.typography.bodyMedium)
            Text(text = "SKU: ${state.skuCode}", style = MaterialTheme.typography.bodyMedium)
            Text(text = "Price: ${state.priceLabel}", style = MaterialTheme.typography.bodyMedium)
            Text(text = "Stock: ${state.stockLabel}", style = MaterialTheme.typography.bodyMedium)
            Text(text = "Status: ${state.availabilityStatus}", style = MaterialTheme.typography.bodyMedium)
        }
        state.errorMessage?.let { message ->
            Text(
                text = message,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.error,
            )
        }
    }
}
