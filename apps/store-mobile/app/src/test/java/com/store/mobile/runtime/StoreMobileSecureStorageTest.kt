package com.store.mobile.runtime

import org.junit.Assert.assertEquals
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Test

class StoreMobileSecureStorageTest {
    @Test
    fun prefersEncryptedStoreWhenAvailable() {
        val encryptedStore = InMemoryStoreMobileKeyValueStore()
        val fallbackStore = InMemoryStoreMobileKeyValueStore()

        val bootstrap = resolveStoreMobileSecureStorage(
            encryptedStoreFactory = { encryptedStore },
            fallbackStoreFactory = { fallbackStore },
        )

        assertSame(encryptedStore, bootstrap.keyValueStore)
        assertEquals(StoreMobileStorageSecurityPosture.ENCRYPTED, bootstrap.securityPosture)
        assertTrue(bootstrap.detail.contains("Encrypted"))
    }

    @Test
    fun fallsBackToPlainPreferencesWhenEncryptedStorageCannotBeCreated() {
        val fallbackStore = InMemoryStoreMobileKeyValueStore()

        val bootstrap = resolveStoreMobileSecureStorage(
            encryptedStoreFactory = { throw IllegalStateException("Android keystore unavailable") },
            fallbackStoreFactory = { fallbackStore },
        )

        assertSame(fallbackStore, bootstrap.keyValueStore)
        assertEquals(StoreMobileStorageSecurityPosture.FALLBACK_UNENCRYPTED, bootstrap.securityPosture)
        assertTrue(bootstrap.detail.contains("Android keystore unavailable"))
    }
}
