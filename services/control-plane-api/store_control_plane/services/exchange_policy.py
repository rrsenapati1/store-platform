from __future__ import annotations

from dataclasses import dataclass

from .purchase_policy import money


@dataclass(slots=True)
class PaymentAllocationDraft:
    payment_method: str
    amount: float


@dataclass(slots=True)
class ExchangeSettlementDraft:
    sale_return_status: str
    exchange_status: str
    balance_direction: str
    balance_amount: float
    refund_amount: float
    refund_method: str
    payment_allocations: list[PaymentAllocationDraft]


def build_exchange_settlement(
    *,
    credit_note_total: float,
    replacement_total: float,
    settlement_method: str,
    can_approve_refund: bool,
) -> ExchangeSettlementDraft:
    credit_total = money(credit_note_total)
    replacement_grand_total = money(replacement_total)

    if replacement_grand_total > credit_total:
        balance_amount = money(replacement_grand_total - credit_total)
        return ExchangeSettlementDraft(
            sale_return_status="EXCHANGE_SETTLED",
            exchange_status="COMPLETED",
            balance_direction="COLLECT_FROM_CUSTOMER",
            balance_amount=balance_amount,
            refund_amount=0.0,
            refund_method="EXCHANGE_CREDIT",
            payment_allocations=[
                PaymentAllocationDraft(payment_method="EXCHANGE_CREDIT", amount=credit_total),
                PaymentAllocationDraft(payment_method=settlement_method, amount=balance_amount),
            ],
        )

    if replacement_grand_total < credit_total:
        balance_amount = money(credit_total - replacement_grand_total)
        return ExchangeSettlementDraft(
            sale_return_status="REFUND_APPROVED" if can_approve_refund else "REFUND_PENDING_APPROVAL",
            exchange_status="COMPLETED" if can_approve_refund else "REFUND_PENDING_APPROVAL",
            balance_direction="REFUND_TO_CUSTOMER",
            balance_amount=balance_amount,
            refund_amount=balance_amount,
            refund_method=settlement_method,
            payment_allocations=[
                PaymentAllocationDraft(payment_method="EXCHANGE_CREDIT", amount=replacement_grand_total),
            ],
        )

    return ExchangeSettlementDraft(
        sale_return_status="EXCHANGE_SETTLED",
        exchange_status="COMPLETED",
        balance_direction="EVEN",
        balance_amount=0.0,
        refund_amount=0.0,
        refund_method="EXCHANGE_CREDIT",
        payment_allocations=[
            PaymentAllocationDraft(payment_method="EXCHANGE_CREDIT", amount=replacement_grand_total),
        ],
    )
