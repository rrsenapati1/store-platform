from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..dependencies import get_current_actor, get_identity_provider, get_session, get_settings
from ..schemas import ActorBranchMembership, ActorResponse, ActorTenantMembership, OIDCExchangeRequest, SessionTokenResponse
from ..services import ActorContext, AuthService

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/oidc/exchange", response_model=SessionTokenResponse)
async def exchange_oidc_token(
    payload: OIDCExchangeRequest,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    identity_provider=Depends(get_identity_provider),
) -> SessionTokenResponse:
    auth_service = AuthService(session, settings, identity_provider)
    access_token = await auth_service.exchange_oidc_token(payload.token)
    return SessionTokenResponse(access_token=access_token)


@router.get("/me", response_model=ActorResponse)
async def get_me(actor: ActorContext = Depends(get_current_actor)) -> ActorResponse:
    return ActorResponse(
        user_id=actor.user_id,
        email=actor.email,
        full_name=actor.full_name,
        is_platform_admin=actor.is_platform_admin,
        tenant_memberships=[
            ActorTenantMembership(
                tenant_id=membership.tenant_id,
                role_name=membership.role_name,
                status=membership.status,
            )
            for membership in actor.tenant_memberships
        ],
        branch_memberships=[
            ActorBranchMembership(
                tenant_id=membership.tenant_id,
                branch_id=membership.branch_id or "",
                role_name=membership.role_name,
                status=membership.status,
            )
            for membership in actor.branch_memberships
        ],
    )
