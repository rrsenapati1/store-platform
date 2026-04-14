package com.store.mobile.operations

import org.junit.Assert.assertEquals
import org.junit.Test

class ExpiryRepositoryTest {
    @Test
    fun loadsExpiryRecordsForBranch() {
        val repository = InMemoryExpiryRepository()

        val report = repository.loadExpiryReport(branchId = "branch-1")

        assertEquals("BATCH-EXP-1", report.records.first().batchNumber)
    }
}
