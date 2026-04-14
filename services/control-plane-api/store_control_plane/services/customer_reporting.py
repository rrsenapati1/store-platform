from __future__ import annotations

import hashlib

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import CustomerReportingRepository, TenantRepository


_ANONYMOUS_ALIASES = {
    "",
    "anonymous",
    "guest",
    "walk in",
    "walk-in",
    "walkin",
}


def _money(value: float) -> float:
    return round(float(value), 2)


def _normalized(value: str | None) -> str:
    return (value or "").strip().lower()


def _customer_key(*, customer_name: str, customer_gstin: str | None) -> str | None:
    gstin = (customer_gstin or "").strip().upper()
    if gstin:
        return f"gstin:{gstin}"
    normalized_name = _normalized(customer_name)
    if normalized_name in _ANONYMOUS_ALIASES:
        return None
    return f"name:{normalized_name}"


def _customer_id(*, tenant_id: str, customer_key: str) -> str:
    digest = hashlib.sha256(f"{tenant_id}:{customer_key}".encode("utf-8")).hexdigest()
    return digest[:32]


class CustomerReportingService:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._tenant_repo = TenantRepository(session)
        self._reporting_repo = CustomerReportingRepository(session)

    async def list_customer_directory(self, *, tenant_id: str, query: str | None) -> dict[str, object]:
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

        sales = await self._reporting_repo.list_sales(tenant_id=tenant_id)
        customer_index = self._build_customer_index(tenant_id=tenant_id, sales=sales)
        records = []
        query_value = _normalized(query)
        for record in customer_index.values():
            searchable_fields = (record["name"], record["gstin"])
            if query_value and not any(query_value in _normalized(field) for field in searchable_fields):
                continue
            records.append(
                {
                    "customer_id": record["customer_id"],
                    "name": record["name"],
                    "phone": record["phone"],
                    "email": record["email"],
                    "gstin": record["gstin"],
                    "visit_count": record["visit_count"],
                    "lifetime_value": record["lifetime_value"],
                    "last_sale_id": record["last_sale_id"],
                    "last_invoice_number": record["last_invoice_number"],
                    "last_branch_id": record["last_branch_id"],
                }
            )
        records.sort(key=lambda item: (item["name"], item["gstin"] or ""))
        return {"records": records}

    async def get_customer_history(self, *, tenant_id: str, customer_id: str) -> dict[str, object]:
        tenant = await self._tenant_repo.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

        sales = await self._reporting_repo.list_sales(tenant_id=tenant_id)
        customer_index = self._build_customer_index(tenant_id=tenant_id, sales=sales)
        customer = customer_index.get(customer_id)
        if customer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")

        sale_returns = await self._reporting_repo.list_sale_returns(tenant_id=tenant_id)
        exchanges = await self._reporting_repo.list_exchange_orders(tenant_id=tenant_id)

        customer_sales = [sale for sale in sales if sale.sale.id in customer["sale_ids"]]
        sales_records = [
            {
                "sale_id": sale.sale.id,
                "branch_id": sale.sale.branch_id,
                "invoice_id": sale.invoice.id,
                "invoice_number": sale.invoice.invoice_number,
                "grand_total": _money(sale.invoice.grand_total),
                "payment_method": self._payment_method(sale.payments),
            }
            for sale in customer_sales
        ]

        customer_sale_ids = {record["sale_id"] for record in sales_records}
        returns_records = []
        credit_note_totals = {}
        for sale_return in sale_returns:
            if sale_return.sale_return.sale_id not in customer_sale_ids:
                continue
            credit_note = sale_return.credit_note
            returns_records.append(
                {
                    "sale_return_id": sale_return.sale_return.id,
                    "sale_id": sale_return.sale_return.sale_id,
                    "branch_id": sale_return.sale_return.branch_id,
                    "credit_note_id": credit_note.id,
                    "credit_note_number": credit_note.credit_note_number,
                    "grand_total": _money(credit_note.grand_total),
                    "refund_amount": _money(sale_return.sale_return.refund_amount),
                    "status": sale_return.sale_return.status,
                }
            )
            credit_note_totals[sale_return.sale_return.id] = credit_note.grand_total

        sales_by_id = {sale.sale.id: sale for sale in sales}
        exchanges_records = []
        for exchange in exchanges:
            exchange_order = exchange.exchange_order
            if exchange_order.original_sale_id not in customer_sale_ids:
                continue
            replacement_sale = sales_by_id.get(exchange_order.replacement_sale_id)
            return_total = credit_note_totals.get(exchange_order.sale_return_id, 0.0)
            exchanges_records.append(
                {
                    "exchange_order_id": exchange_order.id,
                    "sale_id": exchange_order.original_sale_id,
                    "branch_id": exchange_order.branch_id,
                    "return_total": _money(return_total),
                    "replacement_total": _money(replacement_sale.invoice.grand_total if replacement_sale else 0.0),
                    "balance_direction": exchange_order.balance_direction,
                    "balance_amount": _money(exchange_order.balance_amount),
                }
            )

        return {
            "customer": {
                "customer_id": customer_id,
                "name": customer["name"],
                "phone": None,
                "email": None,
                "gstin": customer["gstin"],
                "visit_count": customer["visit_count"],
                "lifetime_value": customer["lifetime_value"],
                "last_sale_id": customer["last_sale_id"],
            },
            "sales_summary": {
                "sales_count": len(sales_records),
                "sales_total": _money(sum(record["grand_total"] for record in sales_records)),
                "return_count": len(returns_records),
                "credit_note_total": _money(sum(record["grand_total"] for record in returns_records)),
                "exchange_count": len(exchanges_records),
            },
            "sales": sales_records,
            "returns": returns_records,
            "exchanges": exchanges_records,
        }

    async def branch_customer_report(self, *, tenant_id: str, branch_id: str) -> dict[str, object]:
        branch = await self._tenant_repo.get_branch(tenant_id=tenant_id, branch_id=branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")

        sales = await self._reporting_repo.list_sales(tenant_id=tenant_id, branch_id=branch_id)
        sale_returns = await self._reporting_repo.list_sale_returns(tenant_id=tenant_id, branch_id=branch_id)
        exchanges = await self._reporting_repo.list_exchange_orders(tenant_id=tenant_id, branch_id=branch_id)

        customer_records: dict[str, dict[str, object]] = {}
        anonymous_sales_count = 0
        anonymous_sales_total = 0.0
        sales_by_id = {sale.sale.id: sale for sale in sales}

        for sale in sales:
            customer_key = _customer_key(customer_name=sale.sale.customer_name, customer_gstin=sale.sale.customer_gstin)
            if customer_key is None:
                anonymous_sales_count += 1
                anonymous_sales_total += sale.invoice.grand_total
                continue
            customer_id = _customer_id(tenant_id=tenant_id, customer_key=customer_key)
            record = customer_records.setdefault(
                customer_id,
                {
                    "customer_id": customer_id,
                    "customer_name": sale.sale.customer_name,
                    "sales_count": 0,
                    "sales_total": 0.0,
                    "last_invoice_number": None,
                },
            )
            record["sales_count"] += 1
            record["sales_total"] += sale.invoice.grand_total
            record["last_invoice_number"] = sale.invoice.invoice_number

        return_activity: dict[str, dict[str, object]] = {}
        credit_note_totals = {}
        for sale_return in sale_returns:
            sale = sales_by_id.get(sale_return.sale_return.sale_id)
            if sale is None:
                continue
            customer_key = _customer_key(customer_name=sale.sale.customer_name, customer_gstin=sale.sale.customer_gstin)
            if customer_key is None:
                continue
            customer_id = _customer_id(tenant_id=tenant_id, customer_key=customer_key)
            record = return_activity.setdefault(
                customer_id,
                {
                    "customer_id": customer_id,
                    "customer_name": sale.sale.customer_name,
                    "return_count": 0,
                    "credit_note_total": 0.0,
                    "exchange_count": 0,
                },
            )
            record["return_count"] += 1
            record["credit_note_total"] += sale_return.credit_note.grand_total
            credit_note_totals[sale_return.sale_return.id] = sale_return.credit_note.grand_total

        for exchange in exchanges:
            sale = sales_by_id.get(exchange.exchange_order.original_sale_id)
            if sale is None:
                continue
            customer_key = _customer_key(customer_name=sale.sale.customer_name, customer_gstin=sale.sale.customer_gstin)
            if customer_key is None:
                continue
            customer_id = _customer_id(tenant_id=tenant_id, customer_key=customer_key)
            record = return_activity.setdefault(
                customer_id,
                {
                    "customer_id": customer_id,
                    "customer_name": sale.sale.customer_name,
                    "return_count": 0,
                    "credit_note_total": 0.0,
                    "exchange_count": 0,
                },
            )
            record["exchange_count"] += 1

        top_customers = sorted(
            [
                {
                    **record,
                    "sales_total": _money(record["sales_total"]),
                }
                for record in customer_records.values()
            ],
            key=lambda record: (-record["sales_total"], -record["sales_count"], record["customer_name"]),
        )
        return_records = sorted(
            [
                {
                    **record,
                    "credit_note_total": _money(record["credit_note_total"]),
                }
                for record in return_activity.values()
                if record["return_count"] > 0 or record["exchange_count"] > 0
            ],
            key=lambda record: (-record["credit_note_total"], -record["exchange_count"], record["customer_name"]),
        )
        return {
            "branch_id": branch_id,
            "customer_count": len(customer_records),
            "repeat_customer_count": sum(1 for record in customer_records.values() if record["sales_count"] > 1),
            "anonymous_sales_count": anonymous_sales_count,
            "anonymous_sales_total": _money(anonymous_sales_total),
            "top_customers": top_customers,
            "return_activity": return_records,
        }

    def _build_customer_index(self, *, tenant_id: str, sales) -> dict[str, dict[str, object]]:
        customer_index: dict[str, dict[str, object]] = {}
        for sale in sales:
            customer_key = _customer_key(customer_name=sale.sale.customer_name, customer_gstin=sale.sale.customer_gstin)
            if customer_key is None:
                continue
            customer_id = _customer_id(tenant_id=tenant_id, customer_key=customer_key)
            record = customer_index.setdefault(
                customer_id,
                {
                    "customer_id": customer_id,
                    "name": sale.sale.customer_name,
                    "phone": None,
                    "email": None,
                    "gstin": sale.sale.customer_gstin,
                    "visit_count": 0,
                    "lifetime_value": 0.0,
                    "last_sale_id": None,
                    "last_invoice_number": None,
                    "last_branch_id": None,
                    "last_sort_key": None,
                    "sale_ids": [],
                },
            )
            record["visit_count"] += 1
            record["lifetime_value"] += sale.invoice.grand_total
            record["sale_ids"].append(sale.sale.id)
            sort_key = (sale.invoice.issued_on, sale.invoice.invoice_number)
            if record["last_sort_key"] is None or sort_key >= record["last_sort_key"]:
                record["last_sort_key"] = sort_key
                record["last_sale_id"] = sale.sale.id
                record["last_invoice_number"] = sale.invoice.invoice_number
                record["last_branch_id"] = sale.sale.branch_id
                record["name"] = sale.sale.customer_name
                record["gstin"] = sale.sale.customer_gstin

        for record in customer_index.values():
            record["lifetime_value"] = _money(record["lifetime_value"])
            record.pop("last_sort_key", None)
        return customer_index

    @staticmethod
    def _payment_method(payments) -> str:
        if len(payments) == 1:
            return payments[0].payment_method
        return "MIXED"
