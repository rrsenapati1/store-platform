from __future__ import annotations

from datetime import timedelta
from secrets import token_urlsafe

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AppSession, PlatformAdminAccount, User
from ..utils import new_id, utc_now


class IdentityRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_user_by_external_subject(self, external_subject: str) -> User | None:
        statement = select(User).where(User.external_subject == external_subject)
        return await self._session.scalar(statement)

    async def get_user_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.lower())
        return await self._session.scalar(statement)

    async def get_user_by_id(self, user_id: str) -> User | None:
        statement = select(User).where(User.id == user_id)
        return await self._session.scalar(statement)

    async def upsert_user(
        self,
        *,
        external_subject: str,
        email: str,
        full_name: str,
        provider: str,
    ) -> User:
        user = await self.get_user_by_external_subject(external_subject)
        if user is None:
            user = await self.get_user_by_email(email)
        if user is None:
            user = User(
                id=new_id(),
                external_subject=external_subject,
                email=email.lower(),
                full_name=full_name,
                provider=provider,
                is_active=True,
                last_login_at=utc_now(),
            )
            self._session.add(user)
        else:
            user.external_subject = external_subject
            user.email = email.lower()
            user.full_name = full_name
            user.provider = provider
            user.is_active = True
            user.last_login_at = utc_now()
        await self._session.flush()
        return user

    async def ensure_platform_admin(self, user_id: str) -> PlatformAdminAccount:
        statement = select(PlatformAdminAccount).where(PlatformAdminAccount.user_id == user_id)
        account = await self._session.scalar(statement)
        if account is None:
            account = PlatformAdminAccount(id=new_id(), user_id=user_id)
            self._session.add(account)
            await self._session.flush()
        return account

    async def is_platform_admin(self, user_id: str) -> bool:
        statement = select(PlatformAdminAccount.id).where(PlatformAdminAccount.user_id == user_id)
        return (await self._session.scalar(statement)) is not None

    async def create_session(self, *, user_id: str, ttl_minutes: int) -> AppSession:
        now = utc_now()
        session_record = AppSession(
            id=new_id(),
            user_id=user_id,
            token=token_urlsafe(32),
            expires_at=now + timedelta(minutes=ttl_minutes),
            last_seen_at=now,
        )
        self._session.add(session_record)
        await self._session.flush()
        return session_record

    async def get_app_session(self, token: str) -> AppSession | None:
        statement = select(AppSession).where(AppSession.token == token)
        return await self._session.scalar(statement)

    async def touch_session(self, session_record: AppSession) -> None:
        session_record.last_seen_at = utc_now()
        await self._session.flush()
