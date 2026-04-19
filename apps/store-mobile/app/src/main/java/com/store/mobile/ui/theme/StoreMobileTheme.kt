package com.store.mobile.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val StoreMobileLightColorScheme = lightColorScheme(
    primary = androidx.compose.ui.graphics.Color(0xFF155EEF),
    onPrimary = androidx.compose.ui.graphics.Color(0xFFFFFFFF),
    secondary = androidx.compose.ui.graphics.Color(0xFF31527A),
    onSecondary = androidx.compose.ui.graphics.Color(0xFFFFFFFF),
    tertiary = androidx.compose.ui.graphics.Color(0xFF0F766E),
    surface = androidx.compose.ui.graphics.Color(0xFFF9FAFB),
    surfaceVariant = androidx.compose.ui.graphics.Color(0xFFE9EEF7),
    background = androidx.compose.ui.graphics.Color(0xFFF5F7FB),
    onBackground = androidx.compose.ui.graphics.Color(0xFF102033),
    onSurface = androidx.compose.ui.graphics.Color(0xFF172B42),
)

private val StoreMobileDarkColorScheme = darkColorScheme(
    primary = androidx.compose.ui.graphics.Color(0xFF91B4FF),
    onPrimary = androidx.compose.ui.graphics.Color(0xFF082045),
    secondary = androidx.compose.ui.graphics.Color(0xFFB7CAE6),
    onSecondary = androidx.compose.ui.graphics.Color(0xFF14263D),
    tertiary = androidx.compose.ui.graphics.Color(0xFF7CDED2),
    surface = androidx.compose.ui.graphics.Color(0xFF0E1623),
    surfaceVariant = androidx.compose.ui.graphics.Color(0xFF182332),
    background = androidx.compose.ui.graphics.Color(0xFF08111B),
    onBackground = androidx.compose.ui.graphics.Color(0xFFF5F7FB),
    onSurface = androidx.compose.ui.graphics.Color(0xFFF1F5FC),
)

@Composable
fun StoreMobileTheme(
    themeMode: StoreMobileThemeMode = StoreMobileThemeMode.SYSTEM,
    content: @Composable () -> Unit,
) {
    val useDarkTheme = when (themeMode) {
        StoreMobileThemeMode.SYSTEM -> isSystemInDarkTheme()
        StoreMobileThemeMode.LIGHT -> false
        StoreMobileThemeMode.DARK -> true
    }
    val colorScheme = if (useDarkTheme) {
        StoreMobileDarkColorScheme
    } else {
        StoreMobileLightColorScheme
    }

    MaterialTheme(
        colorScheme = colorScheme,
        content = content,
    )
}
