# Store API Contract Matrix

Updated: 2026-04-14

This file tracks the canonical Milestone 1 control-plane API contracts. Legacy retail routes are intentionally excluded from this matrix until they are migrated into the new architecture.

## Authentication

## System

### `GET /v1/system/authority-boundary`

- Purpose:
  - publish the current authority contract between the control plane and the legacy retail API
- Response fields:
  - `control_plane_service`
  - `legacy_service`
  - `cutover_phase`
  - `legacy_write_mode`
  - `migrated_domains[]`
  - `legacy_remaining_domains[]`
  - `shutdown_criteria[]`
  - `shutdown_steps[]`

### `POST /v1/auth/oidc/exchange`

- Purpose:
  - resolve a Korsenex-authenticated actor into Store control-plane session context
- Request:
  - Korsenex JWT bearer token payload
- Response:
  - `access_token`
  - `token_type`
- Runtime rule:
  - production validation is JWKS-backed
  - `stub` mode exists only for tests and isolated local fallback

### `GET /v1/auth/me`

- Purpose:
  - return current actor, platform privileges, tenant memberships, and branch memberships
- Response fields:
  - `user_id`
  - `email`
  - `full_name`
  - `is_platform_admin`
  - `tenant_memberships[]`
  - `branch_memberships[]`

## Platform Admin

### `POST /v1/platform/tenants`

- Purpose:
  - create a tenant and initialize onboarding state

### `GET /v1/platform/tenants`

- Purpose:
  - list tenants and onboarding posture
- Response fields:
  - `records[].tenant_id`
  - `records[].name`
  - `records[].slug`
  - `records[].status`
  - `records[].onboarding_status`

### `POST /v1/platform/tenants/{tenant_id}/owner-invites`

- Purpose:
  - invite or bind a Korsenex identity to tenant-owner authority

## Tenant Control Plane

### `GET /v1/tenants/{tenant_id}`

- Purpose:
  - tenant summary and onboarding status

### `POST /v1/tenants/{tenant_id}/branches`

- Purpose:
  - create branch under tenant

### `GET /v1/tenants/{tenant_id}/branches`

- Purpose:
  - list branches for tenant
- Response fields:
  - `records[].branch_id`
  - `records[].tenant_id`
  - `records[].name`
  - `records[].code`
  - `records[].status`

### `POST /v1/tenants/{tenant_id}/memberships`

- Purpose:
  - assign tenant-level role

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/memberships`

- Purpose:
  - assign branch-level role

### `GET /v1/tenants/{tenant_id}/audit-events`

- Purpose:
  - read append-only onboarding and authorization audit events
- Response fields:
  - `records[].action`
  - `records[].entity_type`
  - `records[].entity_id`
  - `records[].created_at`
  - `records[].payload`

### `POST /v1/tenants/{tenant_id}/staff-profiles`

- Purpose:
  - create or refresh a tenant staff profile in the control-plane directory

### `GET /v1/tenants/{tenant_id}/staff-profiles`

- Purpose:
  - read the tenant staff directory with current role and branch attachment context
- Response fields:
  - `records[].id`
  - `records[].email`
  - `records[].full_name`
  - `records[].role_names[]`
  - `records[].branch_ids[]`
  - `records[].user_id`

### `POST /v1/tenants/{tenant_id}/catalog/products`

- Purpose:
  - create a central catalog product under control-plane ownership

### `GET /v1/tenants/{tenant_id}/catalog/products`

- Purpose:
  - read the tenant central catalog foundation
- Response fields:
  - `records[].product_id`
  - `records[].name`
  - `records[].sku_code`
  - `records[].barcode`
  - `records[].hsn_sac_code`
  - `records[].gst_rate`
  - `records[].selling_price`
  - `records[].status`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/catalog-items`

- Purpose:
  - attach a central catalog product to a branch with optional price override

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/catalog-items`

- Purpose:
  - read the branch catalog assignment view
- Response fields:
  - `records[].id`
  - `records[].product_id`
  - `records[].product_name`
  - `records[].sku_code`
  - `records[].barcode`
  - `records[].base_selling_price`
  - `records[].selling_price_override`
  - `records[].effective_selling_price`
  - `records[].availability_status`

### `POST /v1/tenants/{tenant_id}/catalog/products/{product_id}/barcode-allocation`

- Purpose:
  - allocate or normalize a tenant catalog barcode under control-plane ownership
- Request fields:
  - `barcode` optional manual override
- Response fields:
  - `product_id`
  - `barcode`
  - `source`

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/catalog-scan/{barcode}`

- Purpose:
  - resolve a scanned barcode into branch-priced catalog posture and current stock
- Response fields:
  - `product_id`
  - `product_name`
  - `sku_code`
  - `barcode`
  - `selling_price`
  - `stock_on_hand`
  - `availability_status`

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/barcode-label-preview/{product_id}`

- Purpose:
  - build the branch-priced barcode label payload for a catalog product on the new control plane
- Response fields:
  - `product_id`
  - `sku_code`
  - `product_name`
  - `barcode`
  - `price_label`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/devices`

- Purpose:
  - register a branch device under control-plane ownership

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/devices`

- Purpose:
  - list branch devices and assigned staff context
- Response fields:
  - `records[].id`
  - `records[].device_name`
  - `records[].device_code`
  - `records[].session_surface`
  - `records[].assigned_staff_profile_id`
  - `records[].assigned_staff_full_name`

### `POST /v1/tenants/{tenant_id}/suppliers`

- Purpose:
  - create a supplier master record under control-plane procurement authority

### `GET /v1/tenants/{tenant_id}/suppliers`

- Purpose:
  - read the tenant supplier directory
- Response fields:
  - `records[].supplier_id`
  - `records[].name`
  - `records[].gstin`
  - `records[].payment_terms_days`
  - `records[].status`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders`

- Purpose:
  - create a branch purchase order from control-plane supplier and catalog records

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders`

- Purpose:
  - read the branch purchase-order queue
- Response fields:
  - `records[].purchase_order_id`
  - `records[].purchase_order_number`
  - `records[].supplier_id`
  - `records[].supplier_name`
  - `records[].approval_status`
  - `records[].line_count`
  - `records[].ordered_quantity`
  - `records[].grand_total`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/submit-approval`

- Purpose:
  - move a purchase order from `NOT_REQUESTED` or `REJECTED` into `PENDING_APPROVAL`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/purchase-orders/{purchase_order_id}/approve`

- Purpose:
  - approve a pending purchase order and stamp decision notes

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/purchase-approval-report`

- Purpose:
  - read approval posture for branch procurement
- Response fields:
  - `not_requested_count`
  - `pending_approval_count`
  - `approved_count`
  - `rejected_count`
  - `records[].purchase_order_id`
  - `records[].purchase_order_number`
  - `records[].supplier_name`
  - `records[].approval_status`
  - `records[].ordered_quantity`
  - `records[].approval_requested_note`
  - `records[].approval_decision_note`

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/receiving-board`

- Purpose:
  - read receiving posture for branch procurement after purchase-order approval
- Response fields:
  - `blocked_count`
  - `ready_count`
  - `received_count`
  - `records[].purchase_order_id`
  - `records[].purchase_order_number`
  - `records[].supplier_name`
  - `records[].approval_status`
  - `records[].receiving_status`
  - `records[].goods_receipt_id`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts`

- Purpose:
  - create a branch goods receipt from an approved purchase order and post purchase-receipt inventory ledger entries

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts`

- Purpose:
  - read branch goods receipts created from approved purchase orders
- Response fields:
  - `records[].goods_receipt_id`
  - `records[].goods_receipt_number`
  - `records[].purchase_order_id`
  - `records[].purchase_order_number`
  - `records[].supplier_name`
  - `records[].received_on`
  - `records[].received_quantity`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/goods-receipts/{goods_receipt_id}/batch-lots`

- Purpose:
  - record batch lots against a control-plane goods receipt after intake validation
- Request fields:
  - `lots[].product_id`
  - `lots[].batch_number`
  - `lots[].quantity`
  - `lots[].expiry_date`
- Response fields:
  - `goods_receipt_id`
  - `records[].id`
  - `records[].product_id`
  - `records[].batch_number`
  - `records[].quantity`
  - `records[].expiry_date`

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/batch-expiry-report`

- Purpose:
  - read tracked lot posture, expiry risk, and untracked stock gaps for a branch on the new control plane
- Response fields:
  - `branch_id`
  - `tracked_lot_count`
  - `expiring_soon_count`
  - `expired_count`
  - `untracked_stock_quantity`
  - `records[].batch_lot_id`
  - `records[].product_id`
  - `records[].product_name`
  - `records[].batch_number`
  - `records[].expiry_date`
  - `records[].days_to_expiry`
  - `records[].received_quantity`
  - `records[].written_off_quantity`
  - `records[].remaining_quantity`
  - `records[].status`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/batch-lots/{batch_lot_id}/expiry-write-offs`

- Purpose:
  - write off expiring or expired stock from a tracked batch lot and append an `EXPIRY_WRITE_OFF` inventory ledger entry
- Request fields:
  - `quantity`
  - `reason`
- Response fields:
  - `batch_lot_id`
  - `product_id`
  - `product_name`
  - `batch_number`
  - `expiry_date`
  - `received_quantity`
  - `written_off_quantity`
  - `remaining_quantity`
  - `status`
  - `reason`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/purchase-invoices`

- Purpose:
  - create a branch purchase invoice from a control-plane goods receipt and supplier billing context
- Request fields:
  - `goods_receipt_id`
- Response fields:
  - `id`
  - `supplier_id`
  - `goods_receipt_id`
  - `invoice_number`
  - `invoice_date`
  - `due_date`
  - `payment_terms_days`
  - `subtotal`
  - `cgst_total`
  - `sgst_total`
  - `igst_total`
  - `grand_total`
  - `lines[].product_name`
  - `lines[].quantity`
  - `lines[].unit_cost`
  - `lines[].gst_rate`

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/purchase-invoices`

- Purpose:
  - read branch purchase invoices created from control-plane goods receipts
- Response fields:
  - `records[].purchase_invoice_id`
  - `records[].purchase_invoice_number`
  - `records[].supplier_id`
  - `records[].supplier_name`
  - `records[].goods_receipt_id`
  - `records[].goods_receipt_number`
  - `records[].invoice_date`
  - `records[].due_date`
  - `records[].grand_total`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/purchase-invoices/{purchase_invoice_id}/supplier-returns`

- Purpose:
  - create a supplier return credit note against a branch purchase invoice and append `SUPPLIER_RETURN` inventory ledger entries
- Request fields:
  - `lines[].product_id`
  - `lines[].quantity`
- Response fields:
  - `id`
  - `purchase_invoice_id`
  - `supplier_credit_note_number`
  - `issued_on`
  - `subtotal`
  - `cgst_total`
  - `sgst_total`
  - `igst_total`
  - `grand_total`
  - `lines[].product_name`
  - `lines[].quantity`
  - `lines[].unit_cost`
  - `lines[].gst_rate`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/purchase-invoices/{purchase_invoice_id}/supplier-payments`

- Purpose:
  - record a supplier payment against a branch purchase invoice with outstanding-balance validation
- Request fields:
  - `amount`
  - `payment_method`
  - `reference` optional
- Response fields:
  - `id`
  - `purchase_invoice_id`
  - `payment_number`
  - `paid_on`
  - `payment_method`
  - `amount`
  - `reference`

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/supplier-payables-report`

- Purpose:
  - read branch supplier payable posture after purchase invoices, supplier credit notes, and supplier payments
- Response fields:
  - `branch_id`
  - `invoiced_total`
  - `credit_note_total`
  - `paid_total`
  - `outstanding_total`
  - `records[].purchase_invoice_id`
  - `records[].purchase_invoice_number`
  - `records[].supplier_id`
  - `records[].supplier_name`
  - `records[].invoiced_total`
  - `records[].credit_note_total`
  - `records[].paid_total`
  - `records[].outstanding_total`
  - `records[].settlement_status`

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/inventory-ledger`

- Purpose:
  - read append-only inventory ledger entries currently posted by control-plane receiving, batch expiry, and branch stock-control flows
- Response fields:
  - `records[].inventory_ledger_entry_id`
  - `records[].product_id`
  - `records[].product_name`
  - `records[].sku_code`
  - `records[].entry_type`
  - `records[].quantity`
  - `records[].reference_type`
  - `records[].reference_id`

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/inventory-snapshot`

- Purpose:
  - read branch stock-on-hand derived from the append-only inventory ledger after receipts, counts, adjustments, and transfers
- Response fields:
  - `records[].product_id`
  - `records[].product_name`
  - `records[].sku_code`
  - `records[].stock_on_hand`
  - `records[].last_entry_type`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/stock-adjustments`

- Purpose:
  - post a manual branch stock adjustment and append an `ADJUSTMENT` ledger entry

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/stock-counts`

- Purpose:
  - record a branch stock count and append a `COUNT_VARIANCE` ledger entry when counted stock differs from expected stock

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/transfers`

- Purpose:
  - move stock from one branch to another and append matched `TRANSFER_OUT` and `TRANSFER_IN` ledger entries

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/transfer-board`

- Purpose:
  - read inbound and outbound branch transfer posture under the control-plane inventory authority
- Response fields:
  - `outbound_count`
  - `inbound_count`
  - `records[].transfer_order_id`
  - `records[].transfer_number`
  - `records[].direction`
  - `records[].counterparty_branch_name`
  - `records[].product_name`
  - `records[].quantity`
  - `records[].status`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/sales`

- Purpose:
  - create a branch sale, generate a GST invoice, attach payment posture, and append `SALE` inventory ledger entries on the new control plane
- Request fields:
  - `customer_name`
  - `customer_gstin` optional
  - `payment_method`
  - `lines[].product_id`
  - `lines[].quantity`
- Response fields:
  - `id`
  - `invoice_number`
  - `invoice_kind`
  - `irn_status`
  - `subtotal`
  - `cgst_total`
  - `sgst_total`
  - `igst_total`
  - `grand_total`
  - `payment.payment_method`
  - `lines[].product_name`
  - `lines[].quantity`
  - `tax_lines[].tax_type`
  - `tax_lines[].tax_amount`

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/sales`

- Purpose:
  - read branch sales register entries produced by the new billing foundation
- Response fields:
  - `records[].sale_id`
  - `records[].invoice_number`
  - `records[].customer_name`
  - `records[].invoice_kind`
  - `records[].irn_status`
  - `records[].payment_method`
  - `records[].grand_total`
  - `records[].issued_on`

### `GET /v1/tenants/{tenant_id}/customers`

- Purpose:
  - read the tenant customer directory derived from control-plane sales, returns, and exchanges
- Response fields:
  - `records[].customer_id`
  - `records[].name`
  - `records[].phone`
  - `records[].email`
  - `records[].gstin`
  - `records[].visit_count`
  - `records[].lifetime_value`
  - `records[].last_sale_id`
  - `records[].last_invoice_number`
  - `records[].last_branch_id`

### `GET /v1/tenants/{tenant_id}/customers/{customer_id}/history`

- Purpose:
  - read a customer timeline including sales, returns, and exchanges from the control-plane billing ledger
- Response fields:
  - `customer.customer_id`
  - `customer.name`
  - `customer.phone`
  - `customer.email`
  - `customer.gstin`
  - `customer.visit_count`
  - `customer.lifetime_value`
  - `sales_summary.sales_count`
  - `sales_summary.sales_total`
  - `sales_summary.return_count`
  - `sales_summary.credit_note_total`
  - `sales_summary.exchange_count`
  - `sales[].sale_id`
  - `sales[].invoice_number`
  - `sales[].grand_total`
  - `returns[].sale_return_id`
  - `returns[].credit_note_number`
  - `returns[].grand_total`
  - `exchanges[].exchange_order_id`
  - `exchanges[].balance_direction`

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/customer-report`

- Purpose:
  - read branch customer posture, anonymous sales totals, and return activity for the new control plane
- Response fields:
  - `branch_id`
  - `customer_count`
  - `repeat_customer_count`
  - `anonymous_sales_count`
  - `anonymous_sales_total`
  - `top_customers[].customer_id`
  - `top_customers[].customer_name`
  - `top_customers[].sales_count`
  - `top_customers[].sales_total`
  - `return_activity[].customer_id`
  - `return_activity[].return_count`
  - `return_activity[].credit_note_total`
  - `return_activity[].exchange_count`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/compliance/gst-exports`

- Purpose:
  - create a sales-invoice GST export job and persist IRN-pending compliance posture on the new control plane
- Request fields:
  - `sale_id`
- Response fields:
  - `id`
  - `sale_id`
  - `invoice_id`
  - `invoice_number`
  - `customer_name`
  - `seller_gstin`
  - `buyer_gstin`
  - `hsn_sac_summary`
  - `grand_total`
  - `status`
  - `irn`
  - `ack_no`
  - `signed_qr_payload`
  - `created_at`

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/compliance/gst-exports`

- Purpose:
  - read branch GST export job posture after export creation and IRN attachment on the new control plane
- Response fields:
  - `branch_id`
  - `pending_count`
  - `attached_count`
  - `records[].id`
  - `records[].sale_id`
  - `records[].invoice_id`
  - `records[].invoice_number`
  - `records[].customer_name`
  - `records[].seller_gstin`
  - `records[].buyer_gstin`
  - `records[].hsn_sac_summary`
  - `records[].grand_total`
  - `records[].status`
  - `records[].irn`
  - `records[].ack_no`
  - `records[].signed_qr_payload`
  - `records[].created_at`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/compliance/gst-exports/{job_id}/attach-irn`

- Purpose:
  - attach IRN, ack number, and signed QR payload to a pending GST export job on the new control plane
- Request fields:
  - `irn`
  - `ack_no`
  - `signed_qr_payload`
- Response fields:
  - `id`
  - `sale_id`
  - `invoice_id`
  - `invoice_number`
  - `status`
  - `irn`
  - `ack_no`
  - `signed_qr_payload`
  - `created_at`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/sales/{sale_id}/returns`

- Purpose:
  - create a branch sale return, generate a credit note, and append `CUSTOMER_RETURN` inventory ledger entries on the new control plane
- Request fields:
  - `refund_amount`
  - `refund_method`
  - `lines[].product_id`
  - `lines[].quantity`
- Response fields:
  - `id`
  - `sale_id`
  - `status`
  - `refund_amount`
  - `refund_method`
  - `lines[].product_name`
  - `lines[].quantity`
  - `credit_note.credit_note_number`
  - `credit_note.grand_total`
  - `credit_note.tax_lines[].tax_type`
  - `credit_note.tax_lines[].tax_amount`

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/sale-returns`

- Purpose:
  - read branch sale-return and refund-approval posture produced by the new billing foundation
- Response fields:
  - `records[].sale_return_id`
  - `records[].sale_id`
  - `records[].invoice_number`
  - `records[].customer_name`
  - `records[].status`
  - `records[].refund_amount`
  - `records[].refund_method`
  - `records[].credit_note_number`
  - `records[].credit_note_total`
  - `records[].issued_on`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/sale-returns/{sale_return_id}/approve-refund`

- Purpose:
  - approve a pending refund and persist owner decision posture for the branch sale return
- Request fields:
  - `note` optional
- Response fields:
  - `id`
  - `status`
  - `refund_amount`
  - `refund_method`
  - `credit_note.credit_note_number`
  - `credit_note.grand_total`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/sales/{sale_id}/exchanges`

- Purpose:
  - create a customer exchange by pairing a control-plane sale return, replacement sale, and exchange-order settlement record
- Request fields:
  - `settlement_method`
  - `return_lines[].product_id`
  - `return_lines[].quantity`
  - `replacement_lines[].product_id`
  - `replacement_lines[].quantity`
- Response fields:
  - `id`
  - `original_sale_id`
  - `replacement_sale_id`
  - `sale_return_id`
  - `status`
  - `balance_direction`
  - `balance_amount`
  - `settlement_method`
  - `payment_allocations[].payment_method`
  - `payment_allocations[].amount`
  - `sale_return.credit_note.credit_note_number`
  - `replacement_sale.invoice_number`

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/runtime/devices`

- Purpose:
  - read branch devices that can heartbeat and consume runtime print jobs on the new control plane
- Response fields:
  - `records[].id`
  - `records[].device_name`
  - `records[].device_code`
  - `records[].session_surface`
  - `records[].assigned_staff_profile_id`
  - `records[].assigned_staff_full_name`
  - `records[].last_seen_at`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/runtime/devices/{device_id}/heartbeat`

- Purpose:
  - record branch-device liveness and return queue posture for the selected runtime device
- Response fields:
  - `device_id`
  - `last_seen_at`
  - `queued_job_count`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/runtime/print-jobs/sales/{sale_id}`

- Purpose:
  - queue an invoice print job for a branch runtime device after checkout
- Request fields:
  - `device_id`
  - `copies`
- Response fields:
  - `id`
  - `device_id`
  - `job_type`
  - `status`
  - `reference_type`
  - `reference_id`
  - `payload.title`
  - `payload.lines[]`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/runtime/print-jobs/sale-returns/{sale_return_id}`

- Purpose:
  - queue a credit-note print job for a branch runtime device after sale return creation
- Request fields:
  - `device_id`
  - `copies`
- Response fields:
  - `id`
  - `device_id`
  - `job_type`
  - `status`
  - `reference_type`
  - `reference_id`
  - `payload.title`
  - `payload.lines[]`

### `GET /v1/tenants/{tenant_id}/branches/{branch_id}/runtime/devices/{device_id}/print-jobs`

- Purpose:
  - read queued runtime print jobs assigned to a branch device
- Response fields:
  - `records[].id`
  - `records[].device_id`
  - `records[].job_type`
  - `records[].status`
  - `records[].reference_type`
  - `records[].reference_id`
  - `records[].copies`
  - `records[].payload.title`
  - `records[].payload.lines[]`

### `POST /v1/tenants/{tenant_id}/branches/{branch_id}/runtime/devices/{device_id}/print-jobs/{print_job_id}/complete`

- Purpose:
  - mark a queued runtime print job as completed or failed after the branch device handles it
- Request fields:
  - `status`
  - `failure_reason` optional
- Response fields:
  - `id`
  - `device_id`
  - `job_type`
  - `status`
  - `failure_reason`
  - `reference_type`
  - `reference_id`

## Contract Rule

If any of the contracts above change during implementation, this file must be updated in the same patch.
