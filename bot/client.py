import httpx

from settings import BOT_TOKEN


class BotApiClient:
    LONG_POLLING_TIMEOUT = 60
    BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

    def __init__(self):
        self.last_update_id = None
        self.http_client = httpx.AsyncClient()
        self.headers = {"Content-Type": "application/json"}

    @property
    def offset(self):
        return self.last_update_id + 1 if self.last_update_id else None

    async def get_updates(self):
        resp = await self.http_client.get(
            f"{self.BASE_URL}/getUpdates",
            timeout=self.LONG_POLLING_TIMEOUT + 5,
            params={
                "offset": self.offset,
                "timeout": self.LONG_POLLING_TIMEOUT,
            },
            headers=self.headers,
        )

        if data := resp.json():
            if updates := data["result"]:
                last_update = updates[-1]
                self.last_update_id = last_update["update_id"]
                return updates

        return []

    async def _post(self, method, **params):
        return await self.http_client.post(
            f"{self.BASE_URL}/{method}", headers=self.headers, **params,
        )

    async def set_my_commands(self, commands):
        return await self._post("setMyCommands", json={"commands": commands})

    async def post_message(self, chat_id, text, parse_mode="HTML"):
        body = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        return await self._post("sendMessage", json=body)

