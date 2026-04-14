from __future__ import annotations

from fastapi import APIRouter, Depends

from ..config import Settings
from ..dependencies import get_settings
from ..schemas import AuthorityBoundaryResponse
from ..services.authority import build_authority_boundary

router = APIRouter(prefix="/v1/system", tags=["system"])


@router.get("/authority-boundary", response_model=AuthorityBoundaryResponse)
async def get_authority_boundary(
    settings: Settings = Depends(get_settings),
) -> AuthorityBoundaryResponse:
    return build_authority_boundary(settings)

