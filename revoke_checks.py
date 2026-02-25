import asyncio
from os import getenv

from aiogram import Bot
from dotenv import load_dotenv

from db_tools import check_all_subscriptions, delete_user_subscription, get_all_users

load_dotenv(".env")
ADMIN = getenv("ADMIN")
TOKEN = getenv("BOT_TOKEN")


def delete_vray_sub(obfuscated_user: str) -> None:
    """Delete obfuscated user sub from VRAY."""
    print(obfuscated_user)


async def main() -> None:
    """Check subscriptions and send messages to users."""
    bot = Bot(token=TOKEN)
    (
        common_data_vray,
        user_ids_tomorrow_ends_vray,
    ) = check_all_subscriptions()

    if isinstance(common_data_vray, str):
        common_data_vray = [common_data_vray]
    if isinstance(user_ids_tomorrow_ends_vray, str):
        user_ids_tomorrow_ends_vray = [user_ids_tomorrow_ends_vray]

    await bot.send_message(
        chat_id=ADMIN,
        text=(
            f"Пользователям:\n"
            f"VRAY {common_data_vray}\n"
            "отменены подписки и удалены из базы."
        ),
    )

    for obfuscated_user in common_data_vray:
        # TODO: instead if condition here should be api call for deleting
        # if delete_obfuscated_user_proxy_conf(obfuscated_user):
        print(f"Deleted VRAY sub for user: {obfuscated_user}")
        delete_user_subscription(obfuscated_user, is_vray=1)

    user_ids_tomorrow_ends_vray = (
        [user_ids_tomorrow_ends_vray]
        if isinstance(user_ids_tomorrow_ends_vray, int)
        else user_ids_tomorrow_ends_vray
    )
    for user_id in user_ids_tomorrow_ends_vray:
        await bot.send_message(
            chat_id=int(user_id),
            text=(
                """Напоминание о том, что ваша подписка на VRAY завтра закончится.
                   Вы можете продлить ее."""
            ),
        )


async def send_message_to_all_users() -> None:
    """Send message to all users."""
    bot = Bot(token=TOKEN)
    all_users = get_all_users()
    for user_id in all_users:
        await bot.send_message(
            chat_id=int(user_id),
            text="Объявление: ",
        )


async def refund() -> None:
    """Refunds payment."""
    bot = Bot(token=TOKEN)
    await bot.refund_star_payment(
        user_id=0,
        telegram_payment_charge_id="",
    )


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(refund())
    # asyncio.run(send_message_to_all_users())
