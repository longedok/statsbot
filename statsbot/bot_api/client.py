import logging

import httpx

from settings import BOT_TOKEN

logger = logging.getLogger(__name__)


class BotApiClient:
    TIMEOUT = 15
    LONG_POLLING_TIMEOUT = 60
    BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

    def __init__(self):
        self.last_update_id = None
        self.http_client = httpx.AsyncClient(timeout=self.TIMEOUT)
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
        url = f"{self.BASE_URL}/{method}"
        resp = await self.http_client.post(url, headers=self.headers, **params)
        logging.debug(
            "POST result: url=%s status=%s body=%s", url, resp.status_code, resp.text
        )
        return resp

    async def set_my_commands(self, commands):
        return await self._post("setMyCommands", json={"commands": commands})

    async def post_message(self, chat_id, text, parse_mode="HTML", reply_markup=None):
        body = {
            "chat_id": chat_id,
            "text": text,
        }
        if parse_mode:
            body["parse_mode"] = parse_mode
        if reply_markup:
            body["reply_markup"] = reply_markup

        return await self._post("sendMessage", json=body)

    async def answer_callback(self, callback_query_id):
        body = {
            "callback_query_id": callback_query_id,
        }

        return await self._post("answerCallbackQuery", json=body)

    async def edit_message_text(
        self, chat_id, message_id, text, parse_mode="HTML", reply_markup=None,
    ):
        body = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        if reply_markup:
            body["reply_markup"] = reply_markup

        return await self._post("editMessageText", json=body)

    async def delete_message(self, chat_id, message_id):
        body = {
            "chat_id": chat_id,
            "message_id": message_id,
        }

        return await self._post("deleteMessage", json=body)

