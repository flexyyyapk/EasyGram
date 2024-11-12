import requests
import asyncio

from typing_extensions import override
from typing import Union

from ..types import Message as BaseMessage

from ..types import (
    User as BaseUser,
    Chat as BaseChat,
    ReplyKeyboardMarkup as BaseRKM,
    KeyboardButton as BaseKB,
    InlineKeyboardMarkup as BaseIKM,
    InlineKeyboardButton as BaseIKB,
    CallbackQuery as BaseCQ,
    ChatType as BaseChT,
    ParseMode as BasePM,
    ContentType as BaseCnT
)

from ..exception import ButtonParameterErorr

class GetMe:
    id = None

    def __init__(self, bot):
        self.id = requests.get(f'https://api.telegram.org/bot{bot.token}/getMe').json()['result']['id']

class KeyboardButton(BaseKB):
    """
    Keyboard object.
    :param text: name
    :return: self
    """
    def __init__(self, text: str):
        super().__init__(text)

class ReplyKeyboardMarkup(BaseRKM):
    """
    ReplyKeyboardMarkup object.
    :param width: row length
    :param resize_keyboard: resize keyboard
    """
    def __init__(self, row_width: int=3, resize_keyboard: bool=False):
        super().__init__(row_width, resize_keyboard)

    @override
    def add(self, *args: Union[str, KeyboardButton]) -> None:
        """
        Добавления Keyboard кнопки.
        :param args: KeyboardButton object or text
        :return: None
        """
        _butt = []

        print(args)
        for butt in args:
            if isinstance(butt, KeyboardButton):
                _butt.append({'text': butt.keyboard['text']})
            else:
                _butt.append({'text': butt})

            if len(_butt) == self.row_width:
                self.keyboards.append(_butt)
                _butt = []
        else:
            if _butt:
                self.keyboards.append(_butt)

class InlineKeyboardButton(BaseIKB):
    def __init__(self, text: str, url: str=None, callback_data: str=None):
        super().__init__(text, url, callback_data)

class InlineKeyboardMarkup(BaseIKM):
    def __init__(self, row_width: int=3):
        super().__init__(row_width)

    @override
    def add(self, *args: Union[InlineKeyboardButton]) -> None:
        """
        Добавления Inline Кнопки.
        :param args: InlineKeyboardButton object
        :return: None
        """
        _butt = []

        print(args)
        for butt in args:
            if isinstance(butt, InlineKeyboardButton):
                _butt.append(butt.keyboard)

            if len(_butt) == self.row_width:
                self.keyboards.append(_butt)
                _butt = []
        else:
            if _butt:
                self.keyboards.append(_butt)

class Message(BaseMessage):
    """
    Async Message object.
    """

    def __init__(self, message, bot):
        super().__init__(message, bot)

    @override
    async def answer(self, text: str, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, parse_mode: str=None) -> None:
        await self.bot.send_message(self.chat.id, text, reply_markup, parse_mode)

class CallbackQuery(BaseCQ):
    """
    Async CallbackQuery object.
    """
    def __init__(self, callback_query: dict, bot):
        super().__init__(callback_query, bot)

    @override
    async def answer(self, text: Union[str, int, float], show_alert: bool=False):
        await self.bot.answer_callback_query(self.id, text, show_alert)

class User(BaseUser):
    def __init__(self, user: dict):
        super().__init__(user)

class Chat(BaseChat):
    def __init__(self, chat: dict):
        super().__init__(chat)

class ChatType(BaseChT):
    def __init__(self):
        super().__init__()

class ParseMode(BasePM):
    def __init__(self):
        super().__init__()

class ContentType(BaseCnT):
    def __init__(self):
        super().__init__()