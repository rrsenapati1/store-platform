package com.store.mobile.runtime

interface StoreMobileHubClient {
    fun fetchManifest(hubBaseUrl: String): StoreMobileHubManifest
    fun redeemActivation(
        hubBaseUrl: String,
        installationId: String,
        activationCode: String,
        requestedSessionSurface: String,
    ): StoreMobileRuntimeSession
}

class FakeStoreMobileHubClient : StoreMobileHubClient {
    override fun fetchManifest(hubBaseUrl: String): StoreMobileHubManifest {
        return StoreMobileHubManifest(
            hubBaseUrl = hubBaseUrl,
            hubDeviceId = "hub-demo-1",
            runtimeProfiles = listOf("mobile_store_spoke", "inventory_tablet_spoke"),
            pairingModes = listOf("qr", "approval_code"),
        )
    }

    override fun redeemActivation(
        hubBaseUrl: String,
        installationId: String,
        activationCode: String,
        requestedSessionSurface: String,
    ): StoreMobileRuntimeSession {
        val runtimeProfile = if (requestedSessionSurface == "inventory_tablet") {
            "inventory_tablet_spoke"
        } else {
            "mobile_store_spoke"
        }
        return StoreMobileRuntimeSession(
            accessToken = "session:$activationCode",
            expiresAt = "2099-01-01T00:00:00Z",
            deviceId = if (runtimeProfile == "inventory_tablet_spoke") "paired-tablet-1" else "paired-mobile-1",
            staffProfileId = "staff-demo-1",
            runtimeProfile = runtimeProfile,
            sessionSurface = requestedSessionSurface,
            tenantId = "tenant-demo-1",
            branchId = "branch-demo-1",
        )
    }
}
