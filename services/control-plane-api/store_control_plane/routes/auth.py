from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..dependencies import get_current_actor, get_identity_provider, get_session, get_settings
from ..dependencies.auth import bearer_scheme
from ..schemas import ActorBranchMembership, ActorResponse, ActorTenantMembership, OIDCExchangeRequest, RuntimeActivationRedeemRequest, RuntimeActivationRedeemResponse, SessionTokenResponse, SignOutResponse, StoreDesktopActivationRedeemRequest, StoreDesktopActivationRedeemResponse, StoreDesktopUnlockRequest, StoreDesktopUnlockResponse
from ..services import ActorContext, AuthService, WorkforceService

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/oidc/exchange", response_model=SessionTokenResponse)
async def exchange_oidc_token(
    payload: OIDCExchangeRequest,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    identity_provider=Depends(get_identity_provider),
) -> SessionTokenResponse:
    auth_service = AuthService(session, settings, identity_provider)
    session_record = await auth_service.exchange_oidc_token(payload.token)
    return SessionTokenResponse(
        access_token=session_record.token,
        expires_at=session_record.expires_at.isoformat(),
    )


@router.post("/store-desktop/activate", response_model=StoreDesktopActivationRedeemResponse)
async def redeem_store_desktop_activation(
    payload: StoreDesktopActivationRedeemRequest,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> StoreDesktopActivationRedeemResponse:
    service = WorkforceService(session)
    response = await service.redeem_store_desktop_activation(
        installation_id=payload.installation_id,
        activation_code=payload.activation_code,
        session_ttl_minutes=settings.session_ttl_minutes,
    )
    return StoreDesktopActivationRedeemResponse(**response)


@router.post("/runtime/activate", response_model=RuntimeActivationRedeemResponse)
async def redeem_runtime_activation(
    payload: RuntimeActivationRedeemRequest,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> RuntimeActivationRedeemResponse:
    service = WorkforceService(session)
    response = await service.redeem_runtime_activation(
        installation_id=payload.installation_id,
        activation_code=payload.activation_code,
        session_ttl_minutes=settings.session_ttl_minutes,
    )
    return RuntimeActivationRedeemResponse(**response)


@router.post("/store-desktop/unlock", response_model=StoreDesktopUnlockResponse)
async def unlock_store_desktop_runtime(
    payload: StoreDesktopUnlockRequest,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> StoreDesktopUnlockResponse:
    service = WorkforceService(session)
    response = await service.unlock_store_desktop_runtime(
        installation_id=payload.installation_id,
        local_auth_token=payload.local_auth_token,
        session_ttl_minutes=settings.session_ttl_minutes,
    )
    return StoreDesktopUnlockResponse(**response)


@router.post("/refresh", response_model=SessionTokenResponse)
async def refresh_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    identity_provider=Depends(get_identity_provider),
) -> SessionTokenResponse:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization")
    auth_service = AuthService(session, settings, identity_provider)
    refreshed_session = await auth_service.refresh_session(credentials.credentials)
    return SessionTokenResponse(
        access_token=refreshed_session.token,
        expires_at=refreshed_session.expires_at.isoformat(),
    )


@router.post("/sign-out", response_model=SignOutResponse)
async def sign_out(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    identity_provider=Depends(get_identity_provider),
) -> SignOutResponse:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization")
    auth_service = AuthService(session, settings, identity_provider)
    await auth_service.sign_out(credentials.credentials)
    return SignOutResponse(status="signed_out")


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
