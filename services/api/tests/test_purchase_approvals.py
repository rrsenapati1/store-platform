from store_api.purchase_approvals import (
    build_purchase_approval_report,
    decide_purchase_order_approval,
    ensure_purchase_order_receivable,
    request_purchase_order_approval,
)


def test_purchase_order_review_transitions_capture_request_and_decision_context():
    purchase_order = {"id": "po-1", "approval_status": "NOT_REQUESTED"}

    request_purchase_order_approval(
        purchase_order=purchase_order,
        note="Restock school notebooks",
        actor_roles=["inventory_admin"],
    )

    assert purchase_order["approval_status"] == "PENDING_APPROVAL"
    assert purchase_order["approval_requested_note"] == "Restock school notebooks"
    assert purchase_order["approval_requested_by_roles"] == ["inventory_admin"]

    decide_purchase_order_approval(
        purchase_order=purchase_order,
        decision="APPROVED",
        note="Budget cleared",
        actor_roles=["tenant_owner"],
    )

    assert purchase_order["approval_status"] == "APPROVED"
    assert purchase_order["approval_decision_note"] == "Budget cleared"
    assert purchase_order["approval_decided_by_roles"] == ["tenant_owner"]


def test_purchase_order_must_be_approved_before_receiving():
    purchase_order = {"id": "po-1", "approval_status": "PENDING_APPROVAL"}

    try:
        ensure_purchase_order_receivable(purchase_order=purchase_order)
    except ValueError as exc:
        assert str(exc) == "Purchase order must be approved before receiving"
    else:
        raise AssertionError("Expected pending purchase order to be blocked from receiving")

    purchase_order["approval_status"] = "APPROVED"
    assert ensure_purchase_order_receivable(purchase_order=purchase_order) is purchase_order


def test_purchase_approval_report_counts_branch_status_and_receiving_posture():
    report = build_purchase_approval_report(
        branch_id="branch-1",
        purchase_orders=[
            {
                "id": "po-pending",
                "branch_id": "branch-1",
                "supplier_id": "supplier-1",
                "approval_status": "PENDING_APPROVAL",
                "lines": [{"product_id": "product-1", "quantity": 6}],
                "approval_requested_note": "Seasonal restock",
            },
            {
                "id": "po-approved",
                "branch_id": "branch-1",
                "supplier_id": "supplier-1",
                "approval_status": "APPROVED",
                "lines": [{"product_id": "product-1", "quantity": 4}],
                "approval_decision_note": "Approved for delivery",
            },
            {
                "id": "po-rejected",
                "branch_id": "branch-1",
                "supplier_id": "supplier-2",
                "approval_status": "REJECTED",
                "lines": [{"product_id": "product-1", "quantity": 3}],
                "approval_decision_note": "Budget on hold",
            },
            {
                "id": "po-draft",
                "branch_id": "branch-1",
                "supplier_id": "supplier-2",
                "approval_status": "NOT_REQUESTED",
                "lines": [{"product_id": "product-1", "quantity": 2}],
            },
            {
                "id": "po-other-branch",
                "branch_id": "branch-2",
                "supplier_id": "supplier-1",
                "approval_status": "PENDING_APPROVAL",
                "lines": [{"product_id": "product-1", "quantity": 99}],
            },
        ],
        suppliers_by_id={
            "supplier-1": {"id": "supplier-1", "name": "Paper Supply Co"},
            "supplier-2": {"id": "supplier-2", "name": "Office Mart"},
        },
        goods_receipts=[
            {"id": "grn-1", "branch_id": "branch-1", "purchase_order_id": "po-approved"},
            {"id": "grn-2", "branch_id": "branch-2", "purchase_order_id": "po-other-branch"},
        ],
    )

    assert report == {
        "branch_id": "branch-1",
        "not_requested_count": 1,
        "pending_approval_count": 1,
        "approved_count": 1,
        "rejected_count": 1,
        "received_count": 1,
        "records": [
            {
                "purchase_order_id": "po-pending",
                "supplier_name": "Paper Supply Co",
                "approval_status": "PENDING_APPROVAL",
                "line_count": 1,
                "ordered_quantity": 6.0,
                "receiving_status": "AWAITING_APPROVAL",
                "approval_requested_note": "Seasonal restock",
                "approval_decision_note": None,
                "goods_receipt_id": None,
            },
            {
                "purchase_order_id": "po-draft",
                "supplier_name": "Office Mart",
                "approval_status": "NOT_REQUESTED",
                "line_count": 1,
                "ordered_quantity": 2.0,
                "receiving_status": "NOT_REQUESTED",
                "approval_requested_note": None,
                "approval_decision_note": None,
                "goods_receipt_id": None,
            },
            {
                "purchase_order_id": "po-approved",
                "supplier_name": "Paper Supply Co",
                "approval_status": "APPROVED",
                "line_count": 1,
                "ordered_quantity": 4.0,
                "receiving_status": "RECEIVED",
                "approval_requested_note": None,
                "approval_decision_note": "Approved for delivery",
                "goods_receipt_id": "grn-1",
            },
            {
                "purchase_order_id": "po-rejected",
                "supplier_name": "Office Mart",
                "approval_status": "REJECTED",
                "line_count": 1,
                "ordered_quantity": 3.0,
                "receiving_status": "BLOCKED",
                "approval_requested_note": None,
                "approval_decision_note": "Budget on hold",
                "goods_receipt_id": None,
            },
        ],
    }
