import asyncio
import base64
import logging
import sys
from os import getenv
from time import sleep
from uuid import uuid4

import requests
from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
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
BACKUP_HOST_URL = getenv("BACKUP_HOST_URL")

VRAY_PRICING = int(getenv("VRAY_PRICING"))

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
        "vray_30": {
            "payload": "vray_30",
            "value": round(VRAY_PRICING * 1),
        },
        "vray_60": {
            "payload": "vray_60",
            "value": round(VRAY_PRICING * 1.9),
        },
        "vray_91": {
            "payload": "vray_91",
            "value": round(VRAY_PRICING * 2.7),
        },
    }


def subscribe_management_kb() -> InlineKeyboardMarkup:
    """
    subscribe management keyboard
    """
    kb = InlineKeyboardBuilder()
    kb.button(
        text="➕ Купить подписку VRAY MIRROR",
        callback_data="subscribe_vray",
        style="success",
    )
    kb.button(
        text="ℹ️  Инструкция и поддержка", callback_data="instruction", style="primary"
    )
    kb.button(
        text="👽 Проверить подписку",
        callback_data="check_end_date_of_subscription",
        style="primary",
    )
    kb.button(text="🫀 Подписка VRAY MIRROR 2.0", callback_data="restore_vray_sub")
    kb.button(text="🫀 Линк VRAY MIRROR 2.0", callback_data="restore_vray_raw")
    kb.button(
        text="🫀 Бэкап подписка VRAY MIRROR v1", callback_data="restore_vray_v1_sub"
    )
    kb.button(text="🫀 Бэкап линк VRAY MIRROR v1", callback_data="restore_vray_v1_raw")
    kb.button(
        text="НАПИСАТЬ В ПОДДЕРЖКУ",
        callback_data="support",
        style="danger",
    )
    kb.adjust(1, 1, 1, 1, 1, 1, 1, 1)
    return kb.as_markup()


def home_kb() -> InlineKeyboardMarkup:
    """
    home keyboard
    """
    kb = InlineKeyboardBuilder()
    kb.button(
        text="➕ Купить подписку VRAY MIRROR",
        callback_data="subscribe_vray",
        style="success",
    )
    kb.button(
        text="Настройка маршрутов",
        callback_data="routing_instruction",
        style="primary",
    )
    kb.button(
        text="НАПИСАТЬ В ПОДДЕРЖКУ",
        callback_data="support",
        style="danger",
    )
    kb.button(text="😢 Назад", callback_data="home")
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()


def accept_kb() -> InlineKeyboardMarkup:
    """
    accept terms of service
    """
    kb = InlineKeyboardBuilder()
    kb.button(text="ПРИНИМАЮ", callback_data="accept", style="success")
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
            await call.message.answer(
                f"Подписка на {SERVICE_NAME} действует до: {str(vray_check)[:-8]}"
            )
        return
    await call.message.answer(
        f"Действующие подписки на {SERVICE_NAME} не найдены!",
    )


# MAIN SERVICE
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
            sub_url = f"{HOST_URL}/save666masterx/{slug}"
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
            sub_url = f"{HOST_URL}/save666masterx/{slug}"
            r = requests.get(sub_url, timeout=20)
            r.raise_for_status()
            raw = r.text.strip()
            raw_compact = "".join(raw.split())
            vless_link = base64.b64decode(raw_compact).decode("utf-8", errors="replace")
            await call.bot.send_message(
                chat_id=call.from_user.id, text="Вставьте следующий URL в приложение:"
            )
            await call.bot.send_message(chat_id=call.from_user.id, text=vless_link)
            return
    await call.message.answer(
        f"Действующая подпискa на {SERVICE_NAME} не найдена!",
    )


# BACKUP SERVICE
@invoices_router.callback_query(F.data.startswith("restore_vray_v1_sub"))
async def restore_vray_v1_sub(call: CallbackQuery) -> None:
    """
    restore sub if exists
    """
    obfuscated_user = get_obfuscated_user(call.from_user.id)
    if obfuscated_user:
        vray_check = check_subscription_end(call.from_user.id, is_vray=1)
        if vray_check:
            slug = get_client_info(f"{obfuscated_user}@vray")
            sub_url = f"{BACKUP_HOST_URL}/save666masterx/{slug}"
            await call.bot.send_message(
                chat_id=call.from_user.id, text="Вставьте следующий URL в приложение:"
            )
            await call.bot.send_message(chat_id=call.from_user.id, text=sub_url)
            return
    await call.message.answer(
        f"Действующая подпискa на {SERVICE_NAME} не найдена!",
    )


@invoices_router.callback_query(F.data.startswith("restore_vray_v1_raw"))
async def restore_vray_v1_raw(call: CallbackQuery) -> None:
    """
    restore vless raw link if sub exists
    """
    obfuscated_user = get_obfuscated_user(call.from_user.id)
    if obfuscated_user:
        vray_check = check_subscription_end(call.from_user.id, is_vray=1)
        if vray_check:
            slug = get_client_info(f"{obfuscated_user}@vray")
            sub_url = f"{BACKUP_HOST_URL}/save666masterx/{slug}"
            r = requests.get(sub_url, timeout=20)
            r.raise_for_status()
            raw = r.text.strip()
            raw_compact = "".join(raw.split())
            vless_link = base64.b64decode(raw_compact).decode("utf-8", errors="replace")
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
    for period in [30, 60, 91]:
        await call.message.answer_invoice(
            title="Приобрести подписку VRAY MIRROR",
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


# PAYMENTS
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
        days = int(message.successful_payment.invoice_payload.split("_")[1])
        add_xui_client(user_id, nickname, uuid_gen, days)
        slug = get_client_info(f"{uuid_gen}@vray")
        sub_url = f"{HOST_URL}/save666masterx/{slug}"
        backup_sub_url = f"{BACKUP_HOST_URL}/save666masterx/{slug}"
        await bot.send_message(
            chat_id=user_id, text="Вставьте следующие URL в приложение:"
        )
        await bot.send_message(chat_id=user_id, text=sub_url)
        await bot.send_message(chat_id=user_id, text=backup_sub_url)
        return

    await message.answer("Подписка продлена.")


# SUPPORT
@invoices_router.callback_query(F.data.startswith("support"))
async def support(call: CallbackQuery) -> None:
    """
    support links
    """
    await call.message.answer(
        """По вопросам поддержки перейдите по <b><a href="https://feel2code.github.io/vray_mirror_web">ССЫЛКЕ</a></b>,
        там указаны все доступные мессенджеры где вам помогут.

        Либо напишите <b><a href="https://t.me/load_it_check_it_quick_rewriteit">СЮДА</a></b>
        """.replace(
            "  ", ""
        ),
        parse_mode="HTML",
        reply_markup=home_kb(),
    )


@invoices_router.callback_query(F.data.startswith("instruction"))
async def get_instruction(call: CallbackQuery) -> None:
    """
    instruction for the service install
    """
    await call.message.answer(
        f"""
        <b>Инструкция по установке {SERVICE_NAME}:</b>

        1. Установите любой удобный для вас клиент на устройство, поддерживающий импорт подписок vless.

        <b>* Для iOS: <a href="https://apps.apple.com/us/app/v2box-v2ray-client/id6446814690">ТЫК</a></b>

        <b>* Для Android: <a href="https://play.google.com/store/apps/details?id=com.v2raytun.android">ТЫК</a></b>

        <b>* Для iOS, Android, Windows, macOS, Linux: <a href="https://www.happ.su/main">ТЫК</a></b>

        2. Приобретите подписку на {SERVICE_NAME} ✅

        3. После оплаты, вам придет ссылка, перейдите по ней или импортируйте в приложение.
           Если вдруг возникнут проблемы, вы можете вручную запросить ссылку в боте,
           нажав на кнопку "🫀 Подписка {SERVICE_NAME}", или "🫀 Линк {SERVICE_NAME}".

        4. Если не хотите выключать/включать приложения для доступа к обычным сайтам,
           нажмите кнопку "Настройка маршрутов" внизу ⬇️

        Приятного пользования!

        По вопросам поддержки перейдите по <b><a href="https://feel2code.github.io/vray_mirror_web">ССЫЛКЕ</a></b>,
        там указаны все доступные мессенджеры где вам помогут.
        """.replace("  ", ""),
        parse_mode="HTML",
        reply_markup=home_kb(),
    )


@invoices_router.callback_query(F.data.startswith("routing_instruction"))
async def get_routing_instruction(call: CallbackQuery) -> None:
    """
    instruction for the routing rules setup
    """
    for instruction_pic in range(1, 4):
        sleep(1)
        await call.message.answer_photo(
            photo=FSInputFile(
                f"/{FS_USER}/vray_mirror_bot/assets/{instruction_pic}.jpg"
            )
        )
    await call.message.answer(
        """
        Чтобы настроить маршруты в v2raytun зайдите в "Настройки",
        затем "Правила от сообщества", выберите интересующие правила
        и нажмите "Подробнее", затем "Установить" и вернитесь назад.
        После этого нажмите "Включить функцию" и перезапустите подключение.

        Так вам не придется больше переключать подключение для доступа к нужным сайтам.
        """.replace("  ", ""),
        reply_markup=home_kb(),
    )


# PRE-CHECKOUT
@invoices_router.pre_checkout_query(F.invoice_payload)
async def pre_checkout_query(query: PreCheckoutQuery) -> None:
    """
    Pre-checkout query handler
    """
    if query.invoice_payload.startswith("vray_30"):
        await query.answer(ok=True)
        return
    if query.invoice_payload.startswith("vray_60"):
        await query.answer(ok=True)
        return
    if query.invoice_payload.startswith("vray_91"):
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
            ознакомьтесь с инструкцией и правилами использования сервиса.

            Сервис {SERVICE_NAME} не предоставляет услуги VPN,
            а лишь помогает настроить доступ к ресурсам компании {SERVICE_NAME}.
            Сервис не предназначен для обхода блокировок и цензуры.
            Сервис не хранит ваши персональные данные, и не обрабатывает их.
            Сервис не несет ответственности за использование сервиса в незаконных целях.

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
