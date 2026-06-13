import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    bot_token: str
    main_admin_id: int
    private_group_id: int
    channel_link: str
    channel_username: str
    support_username: str
    support_phone: str
    payment_card: str
    payment_name: str
    database_path: str

    @classmethod
    def from_env(cls) -> "Config":
        token = os.getenv("BOT_TOKEN", "").strip()
        if not token:
            raise ValueError("BOT_TOKEN muhit o'zgaruvchisi topilmadi")

        group_id = os.getenv("PRIVATE_GROUP_ID", "").strip()
        if not group_id:
            raise ValueError("PRIVATE_GROUP_ID muhit o'zgaruvchisi topilmadi")

        db_path = os.getenv("DATABASE_PATH", "data/bot.db").strip()
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        return cls(
            bot_token=token,
            main_admin_id=int(os.getenv("MAIN_ADMIN_ID", "6857570089")),
            private_group_id=int(group_id),
            channel_link=os.getenv(
                "CHANNEL_LINK", "https://t.me/+bUQj_WkfOAphNzMy"
            ),
            channel_username=os.getenv("CHANNEL_USERNAME", "FxDubbing"),
            support_username=os.getenv("SUPPORT_USERNAME", "X_Dubbing_Support"),
            support_phone=os.getenv("SUPPORT_PHONE", "+998880823927"),
            payment_card=os.getenv("PAYMENT_CARD", "5614 6816 2654 6851"),
            payment_name=os.getenv("PAYMENT_NAME", "N. F"),
            database_path=db_path,
        )


# Obuna muddatlari (kun)
SUBSCRIPTION_DAYS = {
    "1m": 30,
    "3m": 90,
    "6m": 180,
    "12m": 365,
}

SUBSCRIPTION_LABELS = {
    "1m": "1 Oylik",
    "3m": "3 Oylik",
    "6m": "6 Oylik",
    "12m": "1 Yillik",
}

PRICES = {
    "1m": "25 Ming",
    "3m": "50 Ming",
    "6m": "100 Ming",
    "12m": "250 Ming",
}
