from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_current_actor, get_session
from ..schemas import (
    BranchCatalogItemListResponse,
    BranchCatalogItemRecord,
    BranchCatalogItemResponse,
    BranchCatalogItemUpsertRequest,
    BranchPriceTierPriceListResponse,
    BranchPriceTierPriceRecord,
    BranchPriceTierPriceResponse,
    BranchPriceTierPriceUpsertRequest,
    CatalogProductCreateRequest,
    CatalogProductListResponse,
    CatalogProductRecord,
    CatalogProductResponse,
    PriceTierCreateRequest,
    PriceTierListResponse,
    PriceTierRecord,
    PriceTierResponse,
    PriceTierUpdateRequest,
)
from ..services import ActorContext, CatalogService, PriceTierService, assert_branch_any_capability, assert_tenant_capability

router = APIRouter(prefix="/v1/tenants", tags=["catalog"])


@router.post("/{tenant_id}/catalog/products", response_model=CatalogProductResponse)
async def create_catalog_product(
    tenant_id: str,
    payload: CatalogProductCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CatalogProductResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="catalog.manage")
    service = CatalogService(session)
    product = await service.create_product(
        tenant_id=tenant_id,
        actor_user_id=actor.user_id,
        name=payload.name,
        sku_code=payload.sku_code,
        barcode=payload.barcode,
        hsn_sac_code=payload.hsn_sac_code,
        gst_rate=payload.gst_rate,
        mrp=payload.mrp,
        category_code=payload.category_code,
        selling_price=payload.selling_price,
    )
    return CatalogProductResponse.model_validate(product, from_attributes=True)


@router.get("/{tenant_id}/catalog/products", response_model=CatalogProductListResponse)
async def list_catalog_products(
    tenant_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> CatalogProductListResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="catalog.manage")
    service = CatalogService(session)
    records = await service.list_products(tenant_id=tenant_id)
    return CatalogProductListResponse(records=[CatalogProductRecord(**record) for record in records])


@router.post("/{tenant_id}/branches/{branch_id}/catalog-items", response_model=BranchCatalogItemResponse)
async def upsert_branch_catalog_item(
    tenant_id: str,
    branch_id: str,
    payload: BranchCatalogItemUpsertRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> BranchCatalogItemResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="catalog.manage")
    service = CatalogService(session)
    item = await service.upsert_branch_catalog_item(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        product_id=payload.product_id,
        selling_price_override=payload.selling_price_override,
        availability_status=payload.availability_status,
        reorder_point=payload.reorder_point,
        target_stock=payload.target_stock,
    )
    return BranchCatalogItemResponse(**item)


@router.get("/{tenant_id}/branches/{branch_id}/catalog-items", response_model=BranchCatalogItemListResponse)
async def list_branch_catalog_items(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> BranchCatalogItemListResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("catalog.manage", "sales.bill"))
    service = CatalogService(session)
    records = await service.list_branch_catalog_items(tenant_id=tenant_id, branch_id=branch_id)
    return BranchCatalogItemListResponse(records=[BranchCatalogItemRecord(**record) for record in records])


@router.post("/{tenant_id}/price-tiers", response_model=PriceTierResponse)
async def create_price_tier(
    tenant_id: str,
    payload: PriceTierCreateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PriceTierResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="catalog.manage")
    service = PriceTierService(session)
    record = await service.create_price_tier(
        tenant_id=tenant_id,
        actor_user_id=actor.user_id,
        code=payload.code,
        display_name=payload.display_name,
        status_value=payload.status,
    )
    return PriceTierResponse(**record)


@router.patch("/{tenant_id}/price-tiers/{price_tier_id}", response_model=PriceTierResponse)
async def update_price_tier(
    tenant_id: str,
    price_tier_id: str,
    payload: PriceTierUpdateRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PriceTierResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="catalog.manage")
    service = PriceTierService(session)
    record = await service.update_price_tier(
        tenant_id=tenant_id,
        price_tier_id=price_tier_id,
        actor_user_id=actor.user_id,
        display_name=payload.display_name,
        status_value=payload.status,
    )
    return PriceTierResponse(**record)


@router.get("/{tenant_id}/price-tiers", response_model=PriceTierListResponse)
async def list_price_tiers(
    tenant_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> PriceTierListResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="catalog.manage")
    service = PriceTierService(session)
    records = await service.list_price_tiers(tenant_id=tenant_id)
    return PriceTierListResponse(records=[PriceTierRecord(**record) for record in records["records"]])


@router.post("/{tenant_id}/branches/{branch_id}/price-tier-prices", response_model=BranchPriceTierPriceResponse)
async def upsert_branch_price_tier_price(
    tenant_id: str,
    branch_id: str,
    payload: BranchPriceTierPriceUpsertRequest,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> BranchPriceTierPriceResponse:
    assert_tenant_capability(actor, tenant_id=tenant_id, capability="catalog.manage")
    service = PriceTierService(session)
    record = await service.upsert_branch_price_tier_price(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor.user_id,
        product_id=payload.product_id,
        price_tier_id=payload.price_tier_id,
        selling_price=payload.selling_price,
    )
    return BranchPriceTierPriceResponse(**record)


@router.get("/{tenant_id}/branches/{branch_id}/price-tier-prices", response_model=BranchPriceTierPriceListResponse)
async def list_branch_price_tier_prices(
    tenant_id: str,
    branch_id: str,
    actor: ActorContext = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> BranchPriceTierPriceListResponse:
    assert_branch_any_capability(actor, tenant_id=tenant_id, branch_id=branch_id, capabilities=("catalog.manage", "sales.bill"))
    service = PriceTierService(session)
    records = await service.list_branch_price_tier_prices(tenant_id=tenant_id, branch_id=branch_id)
    return BranchPriceTierPriceListResponse(
        records=[BranchPriceTierPriceRecord(**record) for record in records["records"]]
    )
