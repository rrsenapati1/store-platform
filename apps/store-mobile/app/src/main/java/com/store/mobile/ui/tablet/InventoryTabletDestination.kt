package com.store.mobile.ui.tablet

import com.store.mobile.ui.operations.MobileOperationsSection

enum class InventoryTabletDestination(val operationsSection: MobileOperationsSection?) {
    OVERVIEW(null),
    RECEIVING(MobileOperationsSection.RECEIVING),
    STOCK_COUNT(MobileOperationsSection.STOCK_COUNT),
    RESTOCK(MobileOperationsSection.RESTOCK),
    EXPIRY(MobileOperationsSection.EXPIRY),
    SCAN(MobileOperationsSection.SCAN),
    RUNTIME(MobileOperationsSection.RUNTIME),
}

fun defaultInventoryTabletDestination(): InventoryTabletDestination = InventoryTabletDestination.OVERVIEW
