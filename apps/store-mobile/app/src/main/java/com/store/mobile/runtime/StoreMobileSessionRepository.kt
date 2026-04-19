package com.store.mobile.runtime

import org.json.JSONObject

interface StoreMobileSessionRepository {
    fun saveSession(session: StoreMobileRuntimeSession)
    fun loadSession(): StoreMobileRuntimeSession?
    fun clear()
}

class InMemoryStoreMobileSessionRepository : StoreMobileSessionRepository {
    private var session: StoreMobileRuntimeSession? = null

    override fun saveSession(session: StoreMobileRuntimeSession) {
        this.session = session
    }

    override fun loadSession(): StoreMobileRuntimeSession? = session

    override fun clear() {
        session = null
    }
}

class StoreMobilePersistentSessionRepository(
    private val keyValueStore: StoreMobileKeyValueStore,
) : StoreMobileSessionRepository {
    override fun saveSession(session: StoreMobileRuntimeSession) {
        keyValueStore.putString(SESSION_KEY, session.toJson().toString())
    }

    override fun loadSession(): StoreMobileRuntimeSession? {
        val raw = keyValueStore.getString(SESSION_KEY) ?: return null
        return runCatching { JSONObject(raw).toRuntimeSession() }.getOrNull()
    }

    override fun clear() {
        keyValueStore.remove(SESSION_KEY)
    }

    private fun StoreMobileRuntimeSession.toJson(): JSONObject {
        return JSONObject()
            .put("accessToken", accessToken)
            .put("expiresAt", expiresAt)
            .put("deviceId", deviceId)
            .put("staffProfileId", staffProfileId)
            .put("runtimeProfile", runtimeProfile)
            .put("sessionSurface", sessionSurface)
            .put("tenantId", tenantId)
            .put("branchId", branchId)
    }

    private fun JSONObject.toRuntimeSession(): StoreMobileRuntimeSession {
        return StoreMobileRuntimeSession(
            accessToken = getString("accessToken"),
            expiresAt = getString("expiresAt"),
            deviceId = getString("deviceId"),
            staffProfileId = getString("staffProfileId"),
            runtimeProfile = getString("runtimeProfile"),
            sessionSurface = getString("sessionSurface"),
            tenantId = getString("tenantId"),
            branchId = getString("branchId"),
        )
    }

    private companion object {
        const val SESSION_KEY = "store.mobile.runtime_session"
    }
}
