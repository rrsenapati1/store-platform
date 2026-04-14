from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session
from ..schemas import BarcodeAllocationRequest, BarcodeAllocationResponse, BarcodeLabelPreviewResponse, BarcodeScanLookupResponse
from ..services import ActorContext, BarcodeService, assert_branch_any_capability, assert_tenant_capability

router = APIRouter(prefix="/v1/tenants", tags=["barcode"])


@router.post("/{tenant_id}/catalog/products/{product_id}/barcode-allocation", response_model=BarcodeAllocationResponse)
async def allocate_catalog_product_barcode(
    tenant_id: str,
    product_id: str,
    payload: BarcodeAllocationRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> BarcodeAllocationResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="barcode.manage")
    service = BarcodeService(session)
    record = await service.allocate_product_barcode(
        tenant_id=tenant_id,
        product_id=product_id,
        actor_user_id=actor.user_id,
        requested_barcode=payload.barcode,
    )
    return BarcodeAllocationResponse(**record)


@router.get("/{tenant_id}/branches/{branch_id}/catalog-scan/{barcode}", response_model=BarcodeScanLookupResponse)
async def lookup_branch_catalog_scan(
    tenant_id: str,
    branch_id: str,
    barcode: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> BarcodeScanLookupResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("catalog.manage", "sales.bill"))
    service = BarcodeService(session)
    record = await service.lookup_branch_catalog_scan(tenant_id=tenant_id, branch_id=branch_id, barcode=barcode)
    return BarcodeScanLookupResponse(**record)


@router.get("/{tenant_id}/branches/{branch_id}/barcode-label-preview/{product_id}", response_model=BarcodeLabelPreviewResponse)
async def preview_branch_barcode_label(
    tenant_id: str,
    branch_id: str,
    product_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> BarcodeLabelPreviewResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("barcode.manage", "catalog.manage", "sales.bill"))
    service = BarcodeService(session)
    record = await service.preview_branch_barcode_label(
        tenant_id=tenant_id,
        branch_id=branch_id,
        product_id=product_id,
        actor_user_id=actor.user_id,
    )
    return BarcodeLabelPreviewResponse(**record)
