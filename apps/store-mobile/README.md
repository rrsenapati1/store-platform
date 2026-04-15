# Store Mobile

Android-first Kotlin runtime for handheld store operations.

Current slice:

- Android app scaffold
- Jetpack Compose shell
- manual activation and pairing flow for `mobile_store_spoke` and `inventory_tablet_spoke`
- live camera preview barcode scanning with manual fallback for handheld and inventory-tablet shells
- external scanner support through DataWedge-style broadcasts and HID/USB keyboard-wedge input on the scan screen
- receiving, stock count, and expiry operation screens
- branch-runtime status screen for paired spoke devices
- tablet-first inventory shell inside the same Android app
- rugged-scanner diagnostics for `DataWedge`-style external scanner payloads

Planned next:

- real control-plane and branch-hub data sources
- deeper rugged-device vendor integrations beyond the generic DataWedge-style path
- broader V2 hardware and barcode input hardening

## Rugged scanner setup

For `DataWedge`-style rugged Android scanners, configure the device profile to broadcast:

- action: `com.store.mobile.ACTION_BARCODE_SCAN`
- preferred payload key: `com.symbol.datawedge.data_string`
- accepted fallback payload keys: `barcode`, `data`

If the rugged-device profile is misconfigured, Store Mobile now surfaces that posture in both the scan screen and the runtime status screen. Camera/manual entry remain available as fallback.
