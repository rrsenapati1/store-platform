from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..services import ActorContext, AuthService, SyncDeviceContext, SyncRuntimeAuthService


bearer_scheme = HTTPBearer(auto_error=False)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_identity_provider(request: Request):
    return request.app.state.identity_provider


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        yield session


async def get_current_actor(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    identity_provider=Depends(get_identity_provider),
) -> ActorContext:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing authorization")
    auth_service = AuthService(session, settings, identity_provider)
    return await auth_service.get_actor_context(credentials.credentials)


async def get_current_sync_device(
    device_id: str | None = Header(default=None, alias="x-store-device-id"),
    device_secret: str | None = Header(default=None, alias="x-store-device-secret"),
    session: AsyncSession = Depends(get_session),
) -> SyncDeviceContext:
    if not device_id or not device_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing device credentials")
    auth_service = SyncRuntimeAuthService(session)
    return await auth_service.authenticate_hub_device(device_id=device_id, device_secret=device_secret)
