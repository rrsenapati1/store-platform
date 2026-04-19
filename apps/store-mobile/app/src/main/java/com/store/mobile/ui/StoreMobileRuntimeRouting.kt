package com.store.mobile.ui

import com.store.mobile.ui.operations.MobileOperationsSection
import com.store.mobile.ui.tablet.InventoryTabletDestination

fun isStoreMobileScanSectionActive(
    shellMode: StoreMobileShellMode,
    handheldSection: MobileOperationsSection,
    tabletDestination: InventoryTabletDestination,
): Boolean {
    return if (shellMode == StoreMobileShellMode.TABLET) {
        tabletDestination == InventoryTabletDestination.SCAN
    } else {
        handheldSection == MobileOperationsSection.SCAN
    }
}
