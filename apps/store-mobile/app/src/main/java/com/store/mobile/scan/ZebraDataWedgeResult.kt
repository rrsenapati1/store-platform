package com.store.mobile.scan

sealed interface ZebraDataWedgeResult {
    data object Configured : ZebraDataWedgeResult

    data class Error(
        val message: String,
        val resultCode: String? = null,
    ) : ZebraDataWedgeResult
}
