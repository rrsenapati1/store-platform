package com.store.mobile.ui.entry

import com.store.mobile.ui.pairing.PairingSessionStatus
import com.store.mobile.ui.pairing.PairingUiState

data class StoreMobileEntryStatusModel(
    val eyebrow: String,
    val title: String,
    val detail: String,
    val actionHint: String,
)

fun buildStoreMobileEntryStatusModel(state: PairingUiState): StoreMobileEntryStatusModel {
    return when (state.sessionStatus) {
        PairingSessionStatus.EXPIRED -> StoreMobileEntryStatusModel(
            eyebrow = "Session recovery",
            title = "Recover this paired runtime",
            detail = "This device is still paired to its approved branch hub, but the live operator session expired and must be renewed before handheld or tablet work can continue.",
            actionHint = "Redeem a fresh activation or unpair this device before returning to handheld work.",
        )

        PairingSessionStatus.SIGNED_OUT -> StoreMobileEntryStatusModel(
            eyebrow = "Paired runtime",
            title = "Redeem a fresh activation",
            detail = "This device is already approved for the branch and ready for the next associate session. Choose the runtime mode and redeem a new activation to continue.",
            actionHint = "Keep the existing hub assignment, then redeem the next activation when the operator is ready to resume work.",
        )

        PairingSessionStatus.ACTIVE -> StoreMobileEntryStatusModel(
            eyebrow = "Runtime ready",
            title = "Live session already active",
            detail = "A valid runtime session is already present on this device, so Store Mobile can reopen directly into the paired handheld or tablet workflow.",
            actionHint = "Return to the live runtime now, or unpair this device if it needs to be reassigned to another branch workflow.",
        )

        PairingSessionStatus.UNPAIRED -> StoreMobileEntryStatusModel(
            eyebrow = "Activation required",
            title = "Pair this device to a branch hub",
            detail = "Start by connecting the device to its approved branch hub and choosing the right runtime mode for the operator using it today.",
            actionHint = "Choose handheld or inventory tablet mode, then redeem the activation your owner approved for this device.",
        )
    }
}
