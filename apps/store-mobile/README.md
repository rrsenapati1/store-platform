# Store Mobile

Android-first Kotlin runtime for handheld store operations.

Current slice:

- Android app scaffold
- Jetpack Compose shell
- manual activation and pairing flow for `mobile_store_spoke` and `inventory_tablet_spoke`
- live camera preview barcode scanning with manual fallback for handheld and inventory-tablet shells
- receiving, stock count, and expiry operation screens
- branch-runtime status screen for paired spoke devices
- tablet-first inventory shell inside the same Android app

Planned next:

- real control-plane and branch-hub data sources
- rugged-device scanner integrations and richer external scanner support
- broader V2 hardware and barcode input hardening
