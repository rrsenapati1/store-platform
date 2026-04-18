from .auth import router as auth_router
from .batches import router as batches_router
from .barcode import router as barcode_router
from .billing import router as billing_router
from .catalog import router as catalog_router
from .compliance import router as compliance_router
from .commerce import router as commerce_router
from .customers import router as customers_router
from .exchanges import router as exchange_router
from .inventory import router as inventory_router
from .operations import router as operations_router
from .platform import router as platform_router
from .promotions import router as promotions_router
from .procurement_finance import router as procurement_finance_router
from .purchasing import router as purchasing_router
from .reporting import router as reporting_router
from .runtime import router as runtime_router
from .sync_runtime import router as sync_runtime_router
from .supplier_reporting import router as supplier_reporting_router
from .system import router as system_router
from .tenants import router as tenant_router
from .workforce import router as workforce_router

__all__ = [
    "auth_router",
    "batches_router",
    "barcode_router",
    "billing_router",
    "catalog_router",
    "compliance_router",
    "commerce_router",
    "customers_router",
    "exchange_router",
    "inventory_router",
    "operations_router",
    "platform_router",
    "promotions_router",
    "procurement_finance_router",
    "purchasing_router",
    "reporting_router",
    "runtime_router",
    "sync_runtime_router",
    "supplier_reporting_router",
    "system_router",
    "tenant_router",
    "workforce_router",
]
