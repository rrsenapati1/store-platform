# Store Mobile

Android-first Kotlin runtime for handheld store operations.

Current slice:

- Android app scaffold
- Jetpack Compose shell
- manual activation and pairing flow for `mobile_store_spoke` and `inventory_tablet_spoke`
- scan and lookup workflow through the shared barcode path
- receiving, stock count, and expiry operation screens
- branch-runtime status screen for paired spoke devices
- tablet-first inventory shell inside the same Android app

Planned next:

- live camera preview wiring for barcode capture
- real control-plane and branch-hub data sources
- customer-display follow-on slice
