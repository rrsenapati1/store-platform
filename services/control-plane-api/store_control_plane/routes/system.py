from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..dependencies import get_session, get_settings
from ..schemas import AuthorityBoundaryResponse, SystemHealthResponse
from ..services.authority import build_authority_boundary
from ..services.system_status import build_system_health

router = APIRouter(prefix="/v1/system", tags=["system"])


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
) -> SystemHealthResponse:
    return await build_system_health(settings=settings, session=session)


@router.get("/authority-boundary", response_model=AuthorityBoundaryResponse)
async def get_authority_boundary(
    settings: Settings = Depends(get_settings),
) -> AuthorityBoundaryResponse:
    return build_authority_boundary(settings)
