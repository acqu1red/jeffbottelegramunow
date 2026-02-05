import hashlib
import time
from dataclasses import dataclass

import httpx
from aiogram.types import LabeledPrice

from bot.config import get_settings
from bot.db.models import Payment
from bot.db.repository import (
    add_payment,
    get_payment_by_order_id,
    update_payment_status,
)
from bot.security.crypto import decrypt_text, encrypt_text, telegram_id_hash
from bot.services.subscriptions import grant_subscription, log_security_action
from bot.services.tariffs import Tariff, get_tariff


@dataclass(frozen=True)
class InvoiceData:
    title: str
    description: str
    payload: str
    currency: str
    prices: list[LabeledPrice]
    provider_token: str


@dataclass(frozen=True)
class TinkoffPaymentResult:
    ok: bool
    message: str
    telegram_id: int | None
    tariff: Tariff | None
    status: str | None


def build_stars_invoice(tariff: Tariff) -> InvoiceData:
    return InvoiceData(
        title="Доступ к архиву",
        description="Закрытые материалы. Полный доступ.",
        payload=f"sub_{tariff.code}",
        currency="XTR",
        prices=[
            LabeledPrice(
                label=f"Подписка {tariff.months} мес.",
                amount=tariff.price_stars,
            )
        ],
        provider_token="",
    )


def record_payment(
    telegram_id: int,
    amount: int,
    currency: str,
    method: str,
    status: str,
    order_id: str | None = None,
    payload: str | None = None,
) -> Payment:
    settings = get_settings()
    encrypted_id = encrypt_text(settings.fernet_key, str(telegram_id))
    digest = telegram_id_hash(settings.app_secret, telegram_id)
    payment = Payment(
        telegram_id=encrypted_id,
        telegram_id_hash=digest,
        amount=amount,
        currency=currency,
        method=method,
        status=status,
        order_id=order_id,
        payload=payload,
    )
    return add_payment(payment)


def handle_successful_payment(
    telegram_id: int,
    username: str | None,
    payload: str,
    total_amount: int,
) -> Tariff:
    if not payload.startswith("sub_"):
        raise ValueError("Unknown payload")
    tariff_code = payload.replace("sub_", "")
    tariff = get_tariff(tariff_code)
    record_payment(
        telegram_id,
        total_amount,
        "XTR",
        "stars",
        "paid",
        payload=payload,
    )
    grant_subscription(telegram_id, username, tariff.code)
    return tariff


def build_tinkoff_order_id(tariff_code: str, telegram_hash: str) -> str:
    stamp = int(time.time())
    return "sub_%s_%s_%s" % (tariff_code, telegram_hash, stamp)


def build_tinkoff_token(params: dict[str, str], secret: str) -> str:
    items = [secret]
    for key in sorted(params.keys()):
        if key.lower() == "token":
            continue
        value = params[key]
        if value is None:
            continue
        items.append(str(value))
    raw = "".join(items)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_tinkoff_signature(params: dict[str, str]) -> bool:
    settings = get_settings()
    if "Token" not in params:
        return False
    expected = build_tinkoff_token(params, settings.tinkoff_secret)
    return expected == params["Token"]


def build_tinkoff_init_payload(
    telegram_id: int,
    tariff: Tariff,
) -> dict[str, str]:
    settings = get_settings()
    telegram_hash = telegram_id_hash(settings.app_secret, telegram_id)
    order_id = build_tinkoff_order_id(tariff.code, telegram_hash)
    amount_kopeks = tariff.price_rub * 100
    params = {
        "TerminalKey": settings.tinkoff_terminal_key,
        "Amount": str(amount_kopeks),
        "OrderId": order_id,
        "Description": "Доступ к архиву. %s мес." % tariff.months,
        "NotificationURL": (
            settings.webhook_base_url.rstrip("/") + "/webhook/tinkoff"
        ),
    }
    params["Token"] = build_tinkoff_token(params, settings.tinkoff_secret)
    return params


def create_tinkoff_payment_link(telegram_id: int, tariff: Tariff) -> str:
    params = build_tinkoff_init_payload(telegram_id, tariff)
    response = httpx.post(
        "https://securepay.tinkoff.ru/v2/Init",
        json=params,
        timeout=20.0,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("Success"):
        raise RuntimeError("Tinkoff init failed: %s" % data.get("Message"))
    record_payment(
        telegram_id=telegram_id,
        amount=int(params["Amount"]),
        currency="RUB",
        method="tinkoff",
        status="pending",
        order_id=params["OrderId"],
        payload="sub_%s" % tariff.code,
    )
    return data["PaymentURL"]


def _parse_tinkoff_order_id(order_id: str) -> tuple[str, str] | None:
    parts = order_id.split("_")
    if len(parts) < 4 or parts[0] != "sub":
        return None
    tariff_code = parts[1]
    telegram_hash = parts[2]
    return tariff_code, telegram_hash


def resolve_telegram_id_from_hash(telegram_hash: str) -> int | None:
    from bot.db.repository import get_user_by_hash

    settings = get_settings()
    user = get_user_by_hash(telegram_hash)
    if user is None:
        return None
    try:
        return int(decrypt_text(settings.fernet_key, user.telegram_id))
    except Exception:
        return None


def process_tinkoff_webhook(payload: dict[str, str]) -> TinkoffPaymentResult:
    if not verify_tinkoff_signature(payload):
        return TinkoffPaymentResult(
            False,
            "Invalid token",
            None,
            None,
            payload.get("Status"),
        )

    status = payload.get("Status")
    order_id = payload.get("OrderId") or payload.get("OrderID")
    if not order_id:
        return TinkoffPaymentResult(
            False,
            "Missing OrderId",
            None,
            None,
            status,
        )

    parsed = _parse_tinkoff_order_id(order_id)
    if not parsed:
        return TinkoffPaymentResult(False, "Bad OrderId", None, None, status)

    tariff_code, telegram_hash = parsed
    payment = get_payment_by_order_id(order_id)
    if payment:
        update_payment_status(payment.id, status or "unknown")

    if status != "CONFIRMED":
        return TinkoffPaymentResult(
            True,
            "Payment not confirmed",
            None,
            None,
            status,
        )

    telegram_id = resolve_telegram_id_from_hash(telegram_hash)
    if telegram_id is None:
        log_security_action(
            None,
            "tinkoff_user_not_found",
            "order_id=%s" % order_id,
        )
        return TinkoffPaymentResult(True, "User not found", None, None, status)

    tariff = get_tariff(tariff_code)
    grant_subscription(telegram_id, None, tariff.code)
    return TinkoffPaymentResult(True, "Paid", telegram_id, tariff, status)
