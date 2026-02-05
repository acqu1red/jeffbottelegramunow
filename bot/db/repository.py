from contextlib import contextmanager
from datetime import datetime
from typing import Iterable

from sqlalchemy import and_, select

from bot.db.models import Invite, Payment, SecurityLog, User
from bot.db.session import SessionLocal


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_user_by_hash(telegram_id_hash: str) -> User | None:
    with get_session() as session:
        stmt = select(User).where(User.telegram_id_hash == telegram_id_hash)
        return session.execute(stmt).scalars().first()


def upsert_user(user: User) -> User:
    with get_session() as session:
        session.add(user)
        session.flush()
        session.refresh(user)
        return user


def list_expired_users(now: datetime) -> Iterable[User]:
    with get_session() as session:
        stmt = select(User).where(
            and_(
                User.subscription_end.is_not(None),
                User.subscription_end <= now,
                User.is_active.is_(True),
            )
        )
        return list(session.execute(stmt).scalars().all())


def list_users_for_reminder(
    window_start: datetime,
    window_end: datetime,
) -> Iterable[User]:
    with get_session() as session:
        stmt = select(User).where(
            and_(
                User.subscription_end.is_not(None),
                User.subscription_end > window_start,
                User.subscription_end <= window_end,
                User.is_active.is_(True),
            )
        )
        return list(session.execute(stmt).scalars().all())


def update_user_status(user_id: int, is_active: bool) -> None:
    with get_session() as session:
        user = session.get(User, user_id)
        if user is None:
            return
        user.is_active = is_active
        session.add(user)


def update_user_subscription(
    user_id: int,
    subscription_end: datetime,
    tariff: str,
) -> None:
    with get_session() as session:
        user = session.get(User, user_id)
        if user is None:
            return
        user.subscription_end = subscription_end
        user.tariff = tariff
        user.is_active = True
        session.add(user)


def add_payment(payment: Payment) -> Payment:
    with get_session() as session:
        session.add(payment)
        session.flush()
        session.refresh(payment)
        return payment


def get_payment_by_order_id(order_id: str) -> Payment | None:
    with get_session() as session:
        stmt = select(Payment).where(Payment.order_id == order_id)
        return session.execute(stmt).scalars().first()


def update_payment_status(payment_id: int, status: str) -> None:
    with get_session() as session:
        payment = session.get(Payment, payment_id)
        if payment is None:
            return
        payment.status = status
        session.add(payment)


def add_security_log(log: SecurityLog) -> SecurityLog:
    with get_session() as session:
        session.add(log)
        session.flush()
        session.refresh(log)
        return log


def save_invite(invite: Invite) -> Invite:
    with get_session() as session:
        session.add(invite)
        session.flush()
        session.refresh(invite)
        return invite


def get_active_invite_for_user(telegram_id: int) -> Invite | None:
    from bot.config import get_settings
    from bot.security.crypto import telegram_id_hash

    settings = get_settings()
    digest = telegram_id_hash(settings.app_secret, telegram_id)
    with get_session() as session:
        stmt = select(Invite).where(
            and_(
                Invite.telegram_id_hash == digest,
                Invite.is_used.is_(False),
            )
        )
        return session.execute(stmt).scalars().first()


def mark_invite_used(invite_link: str) -> None:
    with get_session() as session:
        stmt = select(Invite).where(Invite.invite_link == invite_link)
        invite = session.execute(stmt).scalars().first()
        if invite is None:
            return
        invite.is_used = True
        session.add(invite)
