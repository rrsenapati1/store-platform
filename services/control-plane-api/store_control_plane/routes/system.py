from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..dependencies import get_session, get_settings
from ..schemas import (
    AuthorityBoundaryResponse,
    SystemEnvironmentContractResponse,
    SystemHealthResponse,
    SystemSecurityControlsResponse,
)
from ..services.authority import build_authority_boundary
from ..services.system_status import build_system_environment_contract, build_system_health

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


@router.get("/security-controls", response_model=SystemSecurityControlsResponse)
async def get_security_controls(
    settings: Settings = Depends(get_settings),
) -> SystemSecurityControlsResponse:
    return SystemSecurityControlsResponse(
        secure_headers_enabled=settings.secure_headers_enabled,
        secure_headers_hsts_enabled=settings.secure_headers_hsts_enabled,
        secure_headers_csp=settings.secure_headers_csp,
        rate_limits={
            "window_seconds": settings.rate_limit_window_seconds,
            "auth_requests": settings.rate_limit_auth_requests,
            "activation_requests": settings.rate_limit_activation_requests,
            "webhook_requests": settings.rate_limit_webhook_requests,
        },
    )


@router.get("/environment-contract", response_model=SystemEnvironmentContractResponse)
async def get_environment_contract(
    settings: Settings = Depends(get_settings),
) -> SystemEnvironmentContractResponse:
    return build_system_environment_contract(settings=settings)
