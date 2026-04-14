package com.store.mobile.runtime

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
