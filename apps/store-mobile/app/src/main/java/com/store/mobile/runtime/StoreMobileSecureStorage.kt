package com.store.mobile.runtime

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

enum class StoreMobileStorageSecurityPosture {
    ENCRYPTED,
    FALLBACK_UNENCRYPTED,
}

data class StoreMobileSecureStorage(
    val keyValueStore: StoreMobileKeyValueStore,
    val securityPosture: StoreMobileStorageSecurityPosture,
    val detail: String,
)

fun resolveStoreMobileSecureStorage(
    encryptedStoreFactory: () -> StoreMobileKeyValueStore,
    fallbackStoreFactory: () -> StoreMobileKeyValueStore,
): StoreMobileSecureStorage {
    return try {
        StoreMobileSecureStorage(
            keyValueStore = encryptedStoreFactory(),
            securityPosture = StoreMobileStorageSecurityPosture.ENCRYPTED,
            detail = "Encrypted storage active for paired-device and runtime session state.",
        )
    } catch (error: Throwable) {
        StoreMobileSecureStorage(
            keyValueStore = fallbackStoreFactory(),
            securityPosture = StoreMobileStorageSecurityPosture.FALLBACK_UNENCRYPTED,
            detail = "Encrypted storage unavailable: ${error.message ?: error::class.java.simpleName}",
        )
    }
}

fun createAndroidStoreMobileSecureStorage(
    context: Context,
    preferencesName: String,
): StoreMobileSecureStorage {
    return resolveStoreMobileSecureStorage(
        encryptedStoreFactory = {
            val masterKey = MasterKey.Builder(context)
                .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
                .build()
            val sharedPreferences = EncryptedSharedPreferences.create(
                context,
                preferencesName,
                masterKey,
                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
            )
            SharedPreferencesStoreMobileKeyValueStore(sharedPreferences)
        },
        fallbackStoreFactory = {
            SharedPreferencesStoreMobileKeyValueStore(
                context.getSharedPreferences(preferencesName, Context.MODE_PRIVATE),
            )
        },
    )
}
