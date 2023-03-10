from typing import List

from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

from core.logging_utils import logger


class AccessMiddleware(BaseMiddleware):
    """Аутентификация — пропускаем сообщения только от заданных Telegram аккаунтов."""

    def __init__(self, access_ids: List[str]):
        self.access_ids = access_ids
        super().__init__()

    async def on_process_message(self, message: types.Message, _):
        logger.debug(f'Bot retrieved message: {message}')
        if int(message.from_user.id) not in [int(access_id) for access_id in self.access_ids]:
            await message.answer("Access Denied")
            raise CancelHandler()
