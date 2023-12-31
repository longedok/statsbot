from utils import get_env_int, get_env

DEFAULT_TZ = get_env("DEFAULT_TZ", "Europe/Moscow")
BOT_TOKEN = get_env("BOT_TOKEN")
API_ID = get_env_int("API_ID")
API_HASH = get_env("API_HASH")
SESSION_PATH = get_env("SESSION_PATH", default="stats-bot")
QDB_HOST = get_env("QDB_HOST", default="questdb")
QDB_INFLUX_PORT = get_env_int("QDB_INFLUX_PORT", default=9009)
QDB_POSTGRES_PORT = get_env_int("QDB_INFLUX_PORT", default=8812)
QDB_USER = get_env("QDB_USER", "admin")
QDB_PASSWORD = get_env("QDB_PASSWORD", "quest")

