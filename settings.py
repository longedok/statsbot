from utils import get_env_int, get_env

CHAT_ID = get_env_int("CHAT_ID", default=1358721783)
DEFAULT_TZ = get_env("DEFAULT_TZ", "Europe/Moscow")
BOT_TOKEN = get_env("BOT_TOKEN")
API_ID = get_env_int("API_ID")
API_HASH = get_env("API_HASH")
SESSION_PATH = get_env("SESSION_PATH", default="stats-bot")

