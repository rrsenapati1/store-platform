package com.store.mobile.runtime

import android.content.SharedPreferences

interface StoreMobileKeyValueStore {
    fun getString(key: String): String?
    fun putString(key: String, value: String)
    fun remove(key: String)
}

class SharedPreferencesStoreMobileKeyValueStore(
    private val sharedPreferences: SharedPreferences,
) : StoreMobileKeyValueStore {
    override fun getString(key: String): String? = sharedPreferences.getString(key, null)

    override fun putString(key: String, value: String) {
        sharedPreferences.edit().putString(key, value).apply()
    }

    override fun remove(key: String) {
        sharedPreferences.edit().remove(key).apply()
    }
}

class InMemoryStoreMobileKeyValueStore : StoreMobileKeyValueStore {
    private val values = linkedMapOf<String, String>()

    override fun getString(key: String): String? = values[key]

    override fun putString(key: String, value: String) {
        values[key] = value
    }

    override fun remove(key: String) {
        values.remove(key)
    }
}
