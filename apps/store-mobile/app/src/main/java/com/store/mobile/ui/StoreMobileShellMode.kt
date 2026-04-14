package com.store.mobile.ui

enum class StoreMobileShellMode {
    HANDHELD,
    TABLET,
}

fun resolveStoreMobileShellMode(runtimeProfile: String?): StoreMobileShellMode {
    return if (runtimeProfile == "inventory_tablet_spoke") {
        StoreMobileShellMode.TABLET
    } else {
        StoreMobileShellMode.HANDHELD
    }
}
