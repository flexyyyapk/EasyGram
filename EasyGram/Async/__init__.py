import aiohttp
from typing import Union, Callable, Optional, BinaryIO, List, Tuple

import asyncio

from .types import (
    Message,
    ReplyKeyboardMarkup,
    GetMe,
    InlineKeyboardMarkup,
    CallbackQuery
)

from ..exception import Telegram

from io import IOBase, BytesIO

import re

class AsyncBot:
    offset = 0
    _message_handlers = []
    _callback_query_handlers = []

    def __init__(self, token: str):
        self.token = token

    async def get_me(self) -> GetMe:
        """
        Информация о боте.
        :return: GetMe object
        """
        return await GetMe(self)

    async def send_message(self, chat_id: Union[int, str], text: Union[int, float, str], reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, parse_mode: str=None) -> Message:
        """
        Отправка сообщений.
        :param chat_id: айди чата
        :param text: текст
        :param reply_markup: кнопки ReplyKeyboardMarkup или InlineKeyboardMarkup
        :param parse_mode: форматирования текста
        :return: Message
        """
        parameters = {
            'chat_id': chat_id,
            'text': text
        }

        if reply_markup is not None:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.keyboards, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.keyboards}

        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode

        async with aiohttp.ClientSession() as session:
            response = session.post(f"https://api.telegram.org/bot{self.token}/sendMessage", json=parameters)

            try:
                _msg = Message((await (await response).json())['result'], self)
            except KeyError:
                raise Telegram((await (await response).json())['description'])

        return _msg

    async def send_photo(self, chat_id: Union[int, str], photo: Union[IOBase, BytesIO, BinaryIO], caption: Union[int, float, str]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, parse_mode: str=None, photo_name: str=None):
        parameters = {
            'chat_id': chat_id
        }

        if photo_name is not None:
            try:
                _type = re.search('.*?\.(\w+)', photo_name).group(1)
                name = photo_name
            except AttributeError:
                name = 'image.png'
                _type = 'png'
        else:
            if hasattr(photo, 'name'):
                name = photo.name
                _type = re.search('.*?\.(\w+)', photo.name).group(1)
            else:
                name = 'image.png'
                _type = 'png'

        if caption is not None:
            parameters['caption'] = caption

        if reply_markup is not None:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.keyboards, 'resize_keyboard': reply_markup.resize}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.keyboards}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode

        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()

            for param in parameters:
                data.add_field(param, str(parameters[param]))

            data.add_field('photo', photo, filename=name, content_type=f'image/{_type}')

            async with session.post(f"https://api.telegram.org/bot{self.token}/sendPhoto", data=data) as response:
                try:
                    _msg = Message((await response.json())['result'], self)
                except KeyError:
                    raise Telegram((await response.json())['description'])

        return _msg

    def message(self, _filters: Callable=None, content_types: Union[str, List[str]]=None, commands: Union[str, List[str]]=None, allowed_chat_type: Union[List[str], Tuple[str], str]=None) -> Callable:
        """
        Декоратор для обработки входящих сообщений.
        :param _filters: лямбда
        :param content_types: тип сообщения
        :param commands: команды
        :param allowed_chat_type: тип группы
        :return: Функцию которую нужно вызвать
        """
        def wrapper(func):
            self._message_handlers.append({'func': func, 'filters': _filters, 'content_types': content_types, 'commands': commands, 'allowed_chat_type': allowed_chat_type})
        return wrapper

    def callback_query(self, _filters: Callable=None, allowed_chat_type: Union[str, List[str], Tuple[str]]=None) -> Callable:
        """
        Декоратор для обработки вызовов InlineKeyboardMarkup кнопки.
        :param _filters: лямбда
        :param allowed_chat_type: тип группы
        :return: Функцию которую нужно вызвать
        """
        def wrapper(func):
            self._callback_query_handlers.append({'func': func, 'filters': _filters, 'allowed_chat_type': allowed_chat_type})
        return wrapper

    async def answer_callback_query(self, chat_id: Union[int, str], text: Union[int, float, str]=None, show_alert: bool=False) -> bool:
        """
        Отправляет ответ на callback-запрос от пользователя.
        :param chat_id: Идентификатор чата, может быть целым числом или строкой.
        :param text: Текст сообщения, который будет показан пользователю в ответ на callback-запрос.
        :param show_alert: Если True, сообщение будет отображаться в виде всплывающего окна (alert).
        :return: Возвращает True, если запрос был успешным, иначе False.
        """
        parameters = {
            'callback_query_id': chat_id,
            'text': str(text),
            'show_alert': show_alert
        }

        print(chat_id)

        async with aiohttp.ClientSession() as session:
            response = await session.post(f"https://api.telegram.org/bot{self.token}/answerCallbackQuery", json=parameters)

            try:
                _msg = (await response.json())['result']
            except KeyError:
                raise Telegram(await response.json()['description'])

        return _msg

    async def polling(self, on_startup: Callable=None, *args) -> None:
        """
        Запускает процесс опроса событий, выполняя указанную функцию при старте.

        :param on_startup: Функция, которая будет вызвана при запуске опроса (например, для инициализации).
        :param args: Дополнительные аргументы, которые будут переданы в функцию on_startup.
        :return: Ничего не возвращает.
        """

        if on_startup is not None:  asyncio.run(on_startup(args))

        while True:
            async with aiohttp.ClientSession() as session:
                updates = await session.get(f'https://api.telegram.org/bot{self.token}/getUpdates', params={"offset": self.offset})

            if updates.status != 200:
                continue

            updates = (await updates.json())["result"]

            for update in updates:
                try:
                    self.offset = update["update_id"] + 1

                    if update.get('message', False):
                        for handler_message in self._message_handlers:
                            if handler_message['filters'] is not None and not handler_message['filters'](Message(update['message'], self)):
                                continue

                            print(1)

                            if handler_message['commands'] is not None and not any(update['message']['text'].startswith('/' + command) for command in handler_message['commands']):
                                continue

                            print(2)

                            if isinstance(handler_message['content_types'], str):
                                if not update['message'].get(handler_message['content_types'], False) or handler_message['content_types'] == 'any':
                                    continue
                            elif isinstance(handler_message['content_types'], list):
                                if not any(update['message'].get(__type, False) for handler_message['content_types'] in __type) or handler_message['content_types'] == 'any':
                                    continue

                            print(3)

                            if isinstance(handler_message['allowed_chat_type'], str):
                                if update['message']['chat']['type'] != handler_message['allowed_chat_type']:
                                    continue
                            elif isinstance(handler_message['allowed_chat_type'], (tuple, list)):
                                if not any(update['message']['chat']['type'] == _chat_type for _chat_type in handler_message['allowed_chat_type']):
                                    continue

                            print(4)

                            message = Message(update['message'], self)
                            await handler_message['func'](message)
                    elif update.get('callback_query', False):
                        for callback in self._callback_query_handlers:
                            if callback['filters'] is not None and not callback['filters'](CallbackQuery(update['callback_query'], self)):
                                continue

                            if isinstance(callback['allowed_chat_type'], str):
                                if update['callback_query']['chat']['type'] != callback['allowed_chat_type']:
                                    continue
                            elif isinstance(callback['allowed_chat_type'], (tuple, list)):
                                if not any(update['callback_query']['chat']['type'] == _chat_type for _chat_type in callback['allowed_chat_type']):
                                    continue

                            callback_query = CallbackQuery(update['callback_query'], self)
                            await callback['func'](callback_query)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
        session.close()

    def executor(self, on_startup: Callable=None, *args) -> None:
        """
        Удобный способ запуска бота.
        :param on_startup: Функция, которая будет вызвана при запуске опроса (например, для инициализации).
        :param args: Дополнительные аргументы, которые будут переданы в функцию on_startup.
        :return: Ничего не возвращает.
        """
        asyncio.run(self.polling())
        if on_startup is not None:  asyncio.run(on_startup(args))