package com.store.mobile.runtime

data class StoreMobileHubManifest(
    val hubBaseUrl: String,
    val hubDeviceId: String,
    val runtimeProfiles: List<String>,
    val pairingModes: List<String>,
)

data class StoreMobilePairedDevice(
    val deviceId: String,
    val installationId: String,
    val runtimeProfile: String,
    val sessionSurface: String,
    val hubBaseUrl: String,
    val tenantId: String,
    val branchId: String,
)

data class StoreMobileRuntimeSession(
    val accessToken: String,
    val expiresAt: String,
    val deviceId: String,
    val staffProfileId: String,
    val runtimeProfile: String,
    val sessionSurface: String,
    val tenantId: String,
    val branchId: String,
)
