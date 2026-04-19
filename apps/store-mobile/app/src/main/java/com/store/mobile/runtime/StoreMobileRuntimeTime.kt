package com.store.mobile.runtime

import java.time.Instant
import java.time.LocalDateTime
import java.time.OffsetDateTime
import java.time.ZoneOffset

internal fun parseStoreMobileExpiryMillis(expiresAt: String): Long? {
    return runCatching { Instant.parse(expiresAt).toEpochMilli() }.getOrNull()
        ?: runCatching { OffsetDateTime.parse(expiresAt).toInstant().toEpochMilli() }.getOrNull()
        ?: runCatching { LocalDateTime.parse(expiresAt).toInstant(ZoneOffset.UTC).toEpochMilli() }.getOrNull()
}
