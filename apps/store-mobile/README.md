# Store Mobile

Android-first Kotlin runtime for handheld store operations.

Current slice:

- Android app scaffold
- Jetpack Compose shell
- manual activation and pairing flow for `mobile_store_spoke` and `inventory_tablet_spoke`
- live camera preview barcode scanning with manual fallback for handheld and inventory-tablet shells
- external scanner support through DataWedge-style broadcasts and HID/USB keyboard-wedge input on the scan screen
- optional one-tap Zebra DataWedge provisioning for supported Zebra Android devices
- receiving, stock count, and expiry operation screens
- branch-runtime status screen for paired spoke devices
- tablet-first inventory shell inside the same Android app
- rugged-scanner diagnostics for `DataWedge`-style external scanner payloads

Planned next:

- real control-plane and branch-hub data sources
- deeper rugged-device vendor integrations beyond the generic path and first Zebra DataWedge provisioning lane
- broader V2 hardware and barcode input hardening

## Rugged scanner setup

For generic rugged Android scanners and cheap external scanner setups, configure the device profile to broadcast:

- action: `com.store.mobile.ACTION_BARCODE_SCAN`
- preferred payload key: `com.symbol.datawedge.data_string`
- accepted fallback payload keys: `barcode`, `data`

If the rugged-device profile is misconfigured, Store Mobile surfaces that posture in both the scan screen and the runtime status screen. Camera/manual entry remain available as fallback.

### Zebra DataWedge setup

On supported Zebra Android devices with DataWedge preinstalled, Store Mobile can now configure its own profile from the scan screen:

- profile name: `Store Mobile`
- app association: `com.store.mobile` and the current `MainActivity`
- output path: intent broadcast to `com.store.mobile.ACTION_BARCODE_SCAN`
- keystroke output: disabled for the Store Mobile profile to avoid duplicate barcode injection

Store Mobile also listens for the Zebra result-action response and surfaces:

- `Zebra DataWedge available`
- `Zebra DataWedge setup in progress`
- `Zebra DataWedge configured`
- `Zebra DataWedge setup failed`

Generic Android phones/tablets remain fully supported without Zebra-specific setup.
