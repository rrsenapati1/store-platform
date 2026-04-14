# Customer Reporting Migration (CP-011D) Design

Date: 2026-04-14  
Owner: Codex  
Status: Draft for user review

## Goal

Migrate the remaining customer reporting surfaces from the legacy retail API to the control plane, covering:

- customer directory
- customer history
- branch customer report

Expose read-only access in `store-desktop` for branch staff, and full reporting in `owner-web`. Ensure authority cutover is explicit.

## Non-Goals

- No customer write operations are added in this slice.
- No sync-runtime, supplier reporting, or compliance expansion beyond this scope.
- No changes to existing billing or inventory data models beyond read aggregation.

## Scope

### Control-plane API (new)

Routes owned by `services/control-plane-api`:

1. `GET /v1/tenants/{tenant_id}/customers`
   - Directory list.
   - Fields:
     - `customer_id`
     - `customer_name`
     - `customer_gstin`
     - `phone`
     - `email`
     - `total_spend`
     - `last_purchase_on`

2. `GET /v1/tenants/{tenant_id}/customers/{customer_id}/history`
   - Per-customer history.
   - Includes: sales, returns, exchanges, refund approvals.
   - Each entry includes invoice/credit note refs and totals.

3. `GET /v1/tenants/{tenant_id}/branches/{branch_id}/customer-report`
   - Branch summary:
     - repeat buyers
     - anonymous billing
     - top tracked customers
     - return/exchange rates

### UI

- `owner-web`:
  - New `OwnerCustomerInsightsSection` (directory, history, branch report).
  - No new shared workspace state; local state within the section.
- `store-desktop`:
  - New `StoreCustomerInsightsSection` (read-only).
  - Provides branch report + customer lookup only.

### Authorization

- Owner-web access: `reports.view`.
- Store-desktop access: read-only, allow `sales.bill` and/or `sales.return` for branch report; directory/history can require `reports.view` if stricter access is needed.

### Authority/Cutover

- Add `customer_reporting` to `migrated_domains` in the control plane manifest.
- Add legacy authority patterns for the legacy customer endpoints so they emit deprecation headers (shadow) and block (cutover).

## Data Sources

All read models pull from control-plane sources:

- sales
- sale returns + credit notes
- exchanges
- refund approvals

