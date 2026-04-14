package com.store.mobile.runtime

interface StoreMobileHubClient {
    fun fetchManifest(hubBaseUrl: String): StoreMobileHubManifest
    fun redeemActivation(
        hubBaseUrl: String,
        installationId: String,
        activationCode: String,
    ): StoreMobileRuntimeSession
}

class FakeStoreMobileHubClient : StoreMobileHubClient {
    override fun fetchManifest(hubBaseUrl: String): StoreMobileHubManifest {
        return StoreMobileHubManifest(
            hubBaseUrl = hubBaseUrl,
            hubDeviceId = "hub-demo-1",
            runtimeProfiles = listOf("mobile_store_spoke"),
            pairingModes = listOf("qr", "approval_code"),
        )
    }

    override fun redeemActivation(
        hubBaseUrl: String,
        installationId: String,
        activationCode: String,
    ): StoreMobileRuntimeSession {
        return StoreMobileRuntimeSession(
            accessToken = "session:$activationCode",
            expiresAt = "2099-01-01T00:00:00",
            deviceId = "paired-mobile-1",
            staffProfileId = "staff-demo-1",
            runtimeProfile = "mobile_store_spoke",
            sessionSurface = "store_mobile",
        )
    }
}
