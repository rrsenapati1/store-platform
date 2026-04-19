package com.store.mobile.ui.handheld

import com.store.mobile.ui.operations.MobileOperationsSection

enum class HandheldRuntimeDestination {
    SCAN,
    TASKS,
    RUNTIME,
}

fun resolveHandheldRuntimeDestination(section: MobileOperationsSection): HandheldRuntimeDestination {
    return when (section) {
        MobileOperationsSection.SCAN -> HandheldRuntimeDestination.SCAN
        MobileOperationsSection.RUNTIME -> HandheldRuntimeDestination.RUNTIME
        MobileOperationsSection.RECEIVING,
        MobileOperationsSection.STOCK_COUNT,
        MobileOperationsSection.RESTOCK,
        MobileOperationsSection.EXPIRY,
        -> HandheldRuntimeDestination.TASKS
    }
}
