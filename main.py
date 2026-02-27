import asyncio
import logging
import sys
from os import getenv
from uuid import uuid4

import requests
from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from db_tools import check_subscription_end, get_obfuscated_user, need_to_update_user
from xui import add_xui_client, get_client_info

logger = logging.getLogger(__name__)
invoices_router = Router(name=__name__)


load_dotenv(".env")
DEMO_REGIME = bool(int(getenv("DEMO_REGIME")))
SERVICE_NAME = getenv("SERVICE_NAME")
ADMIN = getenv("ADMIN")
TOKEN = getenv("BOT_TOKEN")
FS_USER = getenv("FS_USER")
HOST_URL = getenv("HOST_URL")

PRICING = {
    "vray_90": int(getenv("VRAY_90")),
}
dp = Dispatcher()

if DEMO_REGIME:
    ccy = {
        "vray_1": {
            "payload": "vray_90",
            "value": 1,
        },
    }
else:
    ccy = {
        "vray_90": {
            "payload": "vray_90",
            "value": round(PRICING["vray_90"] * 1),
        },
    }


def subscribe_management_kb() -> InlineKeyboardMarkup:
    """
    subscribe management keyboard
    """
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Купить подписку Velvet RAY", callback_data="subscribe_vray")
    kb.button(text="ℹ️  Инструкция и поддержка", callback_data="instruction")
    kb.button(
        text="👽 Проверить подписку", callback_data="check_end_date_of_subscription"
    )
    kb.button(text="✔️ Подписка Velvet RAY", callback_data="restore_vray_sub")
    kb.button(text="🥲 Линк Velvet RAY", callback_data="restore_vray_raw")
    kb.adjust(1, 1, 1, 2)
    return kb.as_markup()


def home_kb() -> InlineKeyboardMarkup:
    """
    home keyboard
    """
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Купить подписку Velvet RAY", callback_data="subscribe_vray")
    kb.button(text="😢 Назад", callback_data="home")
    kb.adjust(1, 1)
    return kb.as_markup()


def accept_kb() -> InlineKeyboardMarkup:
    """
    accept terms of service
    """
    kb = InlineKeyboardBuilder()
    kb.button(text="ПРИНИМАЮ", callback_data="accept")
    kb.adjust(1)
    return kb.as_markup()


@invoices_router.callback_query(F.data.startswith("check_end_date_of_subscription"))
async def check_end_date_of_subscription(call: CallbackQuery) -> None:
    """
    check end date of the subscription
    """
    conf_to_check = get_obfuscated_user(call.from_user.id)
    if conf_to_check:
        vray_check = check_subscription_end(call.from_user.id, is_vray=1)
        if vray_check:
            await call.message.answer(f"""Ваша подписка на {SERVICE_NAME} действует до:
                {str(vray_check)[:-8]}""")
        return
    await call.message.answer(
        f"Действующие подписки на {SERVICE_NAME} не найдены!",
    )


@invoices_router.callback_query(F.data.startswith("restore_vray_sub"))
async def restore_vray_sub(call: CallbackQuery) -> None:
    """
    restore sub if exists
    """
    obfuscated_user = get_obfuscated_user(call.from_user.id)
    if obfuscated_user:
        vray_check = check_subscription_end(call.from_user.id, is_vray=1)
        if vray_check:
            slug = get_client_info(f"{obfuscated_user}@vray")
            sub_url = f"{HOST_URL}/sub/{slug}"
            await call.bot.send_message(
                chat_id=call.from_user.id, text="Вставьте следующий URL в приложение:"
            )
            await call.bot.send_message(chat_id=call.from_user.id, text=sub_url)
            return
    await call.message.answer(
        f"Действующая подпискa на {SERVICE_NAME} не найдена!",
    )


@invoices_router.callback_query(F.data.startswith("restore_vray_raw"))
async def restore_vray_raw(call: CallbackQuery) -> None:
    """
    restore vless raw link if sub exists
    """
    obfuscated_user = get_obfuscated_user(call.from_user.id)
    if obfuscated_user:
        vray_check = check_subscription_end(call.from_user.id, is_vray=1)
        if vray_check:
            slug = get_client_info(f"{obfuscated_user}@vray")
            sub_url = f"{HOST_URL}/sub/{slug}"
            r = requests.get(sub_url, timeout=20)
            r.raise_for_status()
            vless_link = r.text.strip()
            await call.bot.send_message(
                chat_id=call.from_user.id, text="Вставьте следующий URL в приложение:"
            )
            await call.bot.send_message(chat_id=call.from_user.id, text=vless_link)
            return
    await call.message.answer(
        f"Действующая подпискa на {SERVICE_NAME} не найдена!",
    )


@invoices_router.callback_query(F.data.startswith("subscribe_vray"))
async def subscribe_vray(call: CallbackQuery) -> None:
    """
    subscribe to the vray service
    """
    for period in [90]:
        await call.message.answer_invoice(
            title="Приобрести подписку Velvet RAY",
            description=f"Подписка на {period} дней на {SERVICE_NAME}",
            prices=[
                LabeledPrice(
                    label=ccy[f"vray_{period}"]["payload"].title(),
                    amount=ccy[f"vray_{period}"]["value"],
                ),
            ],
            payload=ccy[f"vray_{period}"]["payload"],
            currency="XTR",
        )


@invoices_router.message(F.successful_payment)
async def successful_payment(message: Message, bot: Bot) -> None:
    """
    Successful payment handler and create config file
    then send it to the user
    """
    user_id = message.from_user.id
    uuid_gen = str(uuid4())[:13]
    nickname = message.from_user.username

    if DEMO_REGIME:
        await bot.refund_star_payment(
            user_id=message.from_user.id,
            telegram_payment_charge_id=message.successful_payment.telegram_payment_charge_id,
        )
        await message.answer("Demo. Your payment has been refunded.")
        need_to_update_user(
            user_id=user_id,
            obfuscated_user=f"{uuid_gen}",
            invoice_payload=message.successful_payment.invoice_payload,
        )
        return

    await message.answer(
        f"""Спасибо за покупку подписки на {SERVICE_NAME}!
        Ваш ID платежа: {message.successful_payment.telegram_payment_charge_id}""",
        message_effect_id="5104841245755180586",  # stars effect
    )
    if not need_to_update_user(
        user_id=user_id,
        obfuscated_user=f"{uuid_gen}",
        invoice_payload=message.successful_payment.invoice_payload,
    ):
        # VRAY
        if message.successful_payment.invoice_payload == "vray_90":
            add_xui_client(user_id, nickname, uuid_gen)
            slug = get_client_info(f"{uuid_gen}@vray")
            sub_url = f"{HOST_URL}/sub/{slug}"
            await bot.send_message(
                chat_id=user_id, text="Вставьте следующий URL в приложение:"
            )
            await bot.send_message(chat_id=user_id, text=sub_url)
            return

    await message.answer("Подписка продлена.")


@invoices_router.callback_query(F.data.startswith("instruction"))
async def get_instruction(call: CallbackQuery) -> None:
    """
    instruction for the service install
    """
    await call.message.answer(
        f"""
        Инструкция по установке {SERVICE_NAME}:
        1. Установите любой удобный для вас клиент на устройство, поддерживающий импорт подписок vless.
        * Для iOS, Android, Windows, macOS, Linux:
          https://www.happ.su/main
        * Для iOS: https://apps.apple.com/us/app/v2box-v2ray-client/id6446814690
        * Для Android: https://play.google.com/store/apps/details?id=com.v2raytun.android
        2. Купите подписку на {SERVICE_NAME}.
        3. После оплаты, вам придет сообщение с подпиской, которую нужно
        импортировать в приложении для подключения.
           Если вдруг возникнут проблемы с импортом, вы можете вручную создать конфигурацию в приложении,
           нажав на кнопку "Подписка Velvet RAY" в боте,
           либо на кнопку "Линк Velvet RAY" и скопировав оттуда URL подписки для импорта.

        Приятного пользования! Подписка на сервис не означает обхода блокировок,
        дает доступ к ресурсам компании {SERVICE_NAME}.

        По вопросам поддержки обращаться к @feel2code
        """.replace("  ", ""),
        reply_markup=home_kb(),
    )


@invoices_router.pre_checkout_query(F.invoice_payload)
async def pre_checkout_query(query: PreCheckoutQuery) -> None:
    """
    Pre-checkout query handler
    """
    if query.invoice_payload.startswith("vray_"):
        await query.answer(ok=True)
        return
    await query.answer(ok=False, error_message="Начните работу с ботом заново. /start")


@invoices_router.callback_query(F.data.startswith("home"))
async def home_menu(call: CallbackQuery) -> None:
    """
    returns user to the home menu
    """
    await call.message.answer(
        f"Вы готовы оформить подписку на {SERVICE_NAME}?",
        reply_markup=subscribe_management_kb(),
    )


@invoices_router.callback_query(F.data.startswith("accept"))
async def accept_call(call: CallbackQuery) -> None:
    """
    returns user to the home menu
    """
    await call.message.answer(
        f"Вы готовы оформить подписку на {SERVICE_NAME}?",
        reply_markup=subscribe_management_kb(),
    )


@invoices_router.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    await message.answer(
        f"""Привет, {html.bold(message.from_user.full_name)}!
            Перед началом использования сервиса и оплаты,
            внимательно ознакомьтесь с инструкцией и правилами использования сервиса.

            Сервис {SERVICE_NAME} не предоставляет услуги VPN,
            а лишь помогает настроить доступ к ресурсам компании {SERVICE_NAME}.
            Сервис не предназначен для обхода блокировок и цензуры.
            Пользователь несет полную ответственность за использование сервиса.
            Сервис не хранит ваши персональные данные, и не обрабатывает их.
            Сервис не несет ответственности за использование сервиса в незаконных целях.
            Сервис шифрует трафик между вашим устройством и ресурсами компании {SERVICE_NAME}.

            Принимая условия сервиса, Вы признаете, что несете
            полную ответственность за использование сервиса.
            Подписка предоставляется на одно устройство.
            Возврат средств не предусмотрен за подписку на сервис,
            оплата происходит единоразово.
            При повторной оплате подписка продлевается.

            Принимаете условия использования сервиса?
        """.replace("  ", ""),
        reply_markup=accept_kb(),
    )


async def main() -> None:
    """Initialize Bot instance with default bot properties which will be passed to all API calls"""
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.include_router(invoices_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    asyncio.run(main())
