from __future__ import annotations

from dataclasses import dataclass

from .billing import CreditNote, ExchangeOrder, Payment, Sale, SaleReturn, SalesInvoice


@dataclass(slots=True)
class CustomerSaleSnapshot:
    sale: Sale
    invoice: SalesInvoice
    payments: list[Payment]


@dataclass(slots=True)
class CustomerSaleReturnSnapshot:
    sale_return: SaleReturn
    credit_note: CreditNote


@dataclass(slots=True)
class CustomerExchangeSnapshot:
    exchange_order: ExchangeOrder
