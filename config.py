import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Majburiy obuna kanallari.
# "id" — get_chat_member uchun kerak: ochiq kanallarda @username, yopiq
# kanallarda esa -100 bilan boshlanuvchi raqamli ID (README.md ga qarang).
CHANNELS = [
    {
        "name": os.getenv("CHANNEL_1_NAME", "1-kanal"),
        "url": os.getenv("CHANNEL_1_URL", "https://t.me/+DK-59zvtQ-5lYmUy"),
        "id": os.getenv("CHANNEL_1_ID", ""),
    },
    {
        "name": os.getenv("CHANNEL_2_NAME", "2-kanal"),
        "url": os.getenv("CHANNEL_2_URL", "https://t.me/+4MqyHPn_QDYxMTFi"),
        "id": os.getenv("CHANNEL_2_ID", ""),
    },
    {
        "name": os.getenv("CHANNEL_3_NAME", "3-kanal"),
        "url": os.getenv("CHANNEL_3_URL", "https://t.me/+LB8c33Lp9DBkYzAy"),
        "id": os.getenv("CHANNEL_3_ID", ""),
    },
    {
        "name": os.getenv("CHANNEL_4_NAME", "4-kanal"),
        "url": os.getenv("CHANNEL_4_URL", "https://t.me/kinoolamiuzbe"),
        "id": os.getenv("CHANNEL_4_ID", "@kinoolamiuzbe"),
    },
    {
        "name": os.getenv("CHANNEL_5_NAME", "5-kanal"),
        "url": os.getenv("CHANNEL_5_URL", "https://t.me/sunniyintellekt_darslar"),
        "id": os.getenv("CHANNEL_5_ID", "@sunniyintellekt_darslar"),
    },
]
