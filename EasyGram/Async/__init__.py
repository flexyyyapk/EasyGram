import aiohttp
import requests
from typing import Union, Callable, Optional, BinaryIO, List, Tuple
import traceback

import asyncio
import time

from bottle import response
from pyrogram.filters import reply

from .types import (
    ParseMode,
    Message,
    ReplyKeyboardMarkup,
    GetMe,
    InlineKeyboardMarkup,
    CallbackQuery,
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeChat,
    BotCommandScopeAllChatAdministrators,
    BotCommandScopeChatMember,
    BotCommandScopeAllGroupChats,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChatAdministrators,
    User,
    InputPollOption,
    InputFile,
    ChatAction
)

from ..exception import Telegram

from io import IOBase, BytesIO

import re

from concurrent.futures import ThreadPoolExecutor

from random import randint
import json

class AsyncBot:
    offset = 0
    _message_handlers = []
    _callback_query_handlers = []
    _next_step_handlers = []

    def __init__(self, token: str):
        self.token = token

    async def get_me(self) -> User:
        """
        Информация о боте.
        :return: GetMe object
        """
        response = requests.post(f'https://api.telegram.org/bot{bot.token}/getMe')

        return User(response.json()['result'])

    def set_my_commands(self, commands: List[BotCommand], scope: Union[BotCommandScopeChat, BotCommandScopeDefault, BotCommandScopeChatMember, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats, BotCommandScopeChatAdministrators, BotCommandScopeAllChatAdministrators]=None, language_code: str=None) -> bool:
        """
        Установка команд в меню команд.
        :param commands: команды
        :param scope: в каком окружении установится команды
        :param language_code: языковой код
        :return: True or False
        """
        parameters = {
            'commands': [{"command": cmd.command, "description": cmd.description} for cmd in commands]
        }

        if scope:
            parameters['scope'] = {"type": scope.type}
            if hasattr(scope, 'chat_id'):
                parameters['scope'].update({"chat_id": scope.chat_id})
            if hasattr(scope, 'user_id'):
                parameters['scope'].update({"user_id": scope.user_id})

        if language_code:
            parameters['language_code'] = language_code

        response = requests.post(f'https://api.telegram.org/bot{self.token}/setMyCommands', json=parameters)

        return bool(response.json()['result'])

    async def send_message(self, chat_id: Union[int, str], text: Union[int, float, str], reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, parse_mode: str=None, reply_to_message_id: int=None) -> Message:
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
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}

        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        async with aiohttp.ClientSession() as session:
            response = session.post(f"https://api.telegram.org/bot{self.token}/sendMessage", json=parameters)

            try:
                _msg = Message((await (await response).json())['result'], self)
            except KeyError:
                raise Telegram((await (await response).json())['description'])

        return _msg

    async def send_photo(self, chat_id: Union[int, str], photo: Union[InputFile], caption: Union[int, float, str]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, parse_mode: str=None, photo_name: str=None, reply_to_message_id: int=None):
        parameters = {
            'chat_id': chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        if photo_name is not None:
            try:
                _type = re.search('.*?\.(\w+)', photo_name).group(1)
                name = photo_name
            except AttributeError:
                name = 'image.png'
                _type = 'png'
        else:
            if hasattr(photo.file, 'name'):
                name = photo.file.name
                _type = re.search('.*?\.(\w+)', photo.file.name).group(1)
            else:
                name = 'image.png'
                _type = 'png'

        if caption is not None:
            parameters['caption'] = caption

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode

        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()

            for param in parameters:
                if param == 'reply_markup':
                    data.add_field(param, json.dumps(parameters[param]))
                    continue
                data.add_field(param, str(parameters[param]))

            data.add_field('photo', photo.file, filename=name, content_type=f'image/{_type}')

            response = await session.post(f"https://api.telegram.org/bot{self.token}/sendPhoto", data=data)
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

    def message_handler(self, _filters: Callable=None, content_types: Union[str, List[str]]=None, commands: Union[str, List[str]]=None, allowed_chat_type: Union[List[str], Tuple[str], str]=None) -> Callable:
        """
        Декоратор для обработки входящих сообщений.Для миграции из aiogram2 в EasyGram
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

    def callback_query_handler(self, _filters: Callable=None, allowed_chat_type: Union[str, List[str], Tuple[str]]=None) -> Callable:
        """
        Декоратор для обработки вызовов InlineKeyboardMarkup кнопки.Для миграции из aiogram2 в EasyGram
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

        async with aiohttp.ClientSession() as session:
            response = await session.post(f"https://api.telegram.org/bot{self.token}/answerCallbackQuery", json=parameters)

            try:
                _msg = (await response.json())['result']
            except KeyError:
                raise Telegram(await response.json()['description'])

        return _msg

    async def delete_message(self, chat_id: Union[int, str], message_id: int) -> bool:
        """
        Удаляет сообщения.
        - Сообщение можно удалить, только если оно было отправлено менее 48 часов назад.
        - Сообщение в приватном чате можно удалить, только если оно было отправлено более 24 часов назад.
        :param chat_id: Айди чата
        :param message_id: Айди сообщения
        :return: Булевое значение
        """
        parameters = {
            'chat_id': chat_id,
            'message_id': message_id
        }

        async with aiohttp.ClientSession() as session:
            response = await session.post(f"https://api.telegram.org/bot{self.token}/deleteMessage", json=parameters)

            _msg = (await response.json())['result']

        return _msg

    async def edit_message_text(self, chat_id: Union[int, str], message_id: int, text: Union[int, float, str], parse_mode: [str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None) -> bool:
        """
        Редактирование сообщения.Обратите внимание, что деловые сообщения, которые не были отправлены ботом и не содержат встроенной клавиатуры, можно редактировать только в течение 48 часов с момента отправки.
        :param chat_id: Айди чата
        :param message_id: Айди сообщения
        :param text: Текст
        :param parse_mode: Форматирования текста
        :param reply_markup: Кнопки
        :return: Булевое значение
        """

        parameters = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": str(text)
        }

        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}

        async with aiohttp.ClientSession() as session:
            response = await session.post(f"https://api.telegram.org/bot{self.token}/editMessageText", json=parameters)

            _msg = (await response.json())['result']

        return _msg

    async def send_poll(self, chat_id: Union[int, str], question: Union[int, float, str], options: List[InputPollOption], question_parse_mode: Union[str, ParseMode]=None, is_anonymous: bool=True, type: str='regular', allows_multiple_answers: bool=False, correct_option_id: int=0, explanation: str=None, explanation_parse_mode: Union[str, ParseMode]=None, open_period: int=None, is_closed: bool=False, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id,
            "question": str(question),
            "type": type,
            "allows_multiple_answers": allows_multiple_answers,
            "is_closed": is_closed
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        if len(options) < 2:
            try:
                raise Telegram('В списке параметра options должно быть минимум 2 элемента.')
            except Telegram as e:
                traceback.print_exc(e)
        else:
            parameters['options'] = []
            for option in options:
                _opt = {"text": option.text}
                if option.text_parse_mode is not None: _opt.update({"text_parse_mode": option.text_parse_mode})
                parameters['options'].append(_opt)

        if type == 'quiz':
            parameters['correct_option_id'] = correct_option_id

        if explanation is not None:
            parameters['explanation'] = explanation
            if explanation_parse_mode is not None: parameters['explanation_parse_mode'] = explanation_parse_mode

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}

        if open_period is not None:
            parameters['open_period'] = open_period

        async with aiohttp.ClientSession() as session:
            response = await session.post(f"https://api.telegram.org/bot{self.token}/sendPoll", json=parameters)

            _msg = Message((await response.json())['result'], self)

        return _msg

    async def send_audio(self, chat_id: Union[int, str], audio: Union[InputFile], title: str=None, caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        if title is None: parameters['title'] = 'audio'
        else: parameters['title'] = title

        parameters['audio'] = audio

        if caption is not None:
            parameters['caption'] = caption

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode

        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()

            for param in parameters:
                if param == 'reply_markup':
                    data.add_field(param, json.loads(parameters[param]))
                    continue
                data.add_field(param, str(parameters[param]))

            async with session.post(f'https://api.telegram.org/bot{self.token}/sendAudio', data=data) as response:
                try:
                    _msg = Message((await response.json())['result'], self)
                except KeyError:
                    raise Telegram((await response.json())['description'])

        return _msg

    async def send_document(self, chat_id: Union[int, str], document: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        parameters['document'] = document

        if caption is not None:
            parameters['caption'] = caption

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode

        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()

            for param in parameters:
                if param == 'reply_markup':
                    data.add_field(param, json.loads(parameters[param]))
                    continue
                data.add_field(param, str(parameters[param]))

            async with session.post(f'https://api.telegram.org/bot{self.token}/sendDocument', data=data) as response:
                try:
                    _msg = Message((await response.json())['result'], self)
                except KeyError:
                    raise Telegram((await response.json())['description'])

        return _msg

    async def send_animation(self, chat_id: Union[int, str], animation: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        parameters['animation'] = animation

        if caption is not None:
            parameters['caption'] = caption

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode

        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()

            for param in parameters:
                if param == 'reply_markup':
                    data.add_field(param, json.loads(parameters[param]))
                    continue
                data.add_field(param, str(parameters[param]))

            async with session.post(f'https://api.telegram.org/bot{self.token}/sendDocument', data=data) as response:
                try:
                    _msg = Message((await response.json())['result'], self)
                except KeyError:
                    raise Telegram((await response.json())['description'])

        return _msg

    async def send_voice(self, chat_id: Union[int, str], voice: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        parameters['voice'] = voice

        if caption is not None:
            parameters['caption'] = caption

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode

        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()

            for param in parameters:
                if param == 'reply_markup':
                    data.add_field(param, json.loads(parameters[param]))
                    continue
                data.add_field(param, str(parameters[param]))

            async with session.post(f'https://api.telegram.org/bot{self.token}/sendVoice', data=data) as response:
                try:
                    _msg = Message((await response.json())['result'], self)
                except KeyError:
                    raise Telegram((await response.json())['description'])

        return _msg

    async def send_video_note(self, chat_id: Union[int, str], video_note: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        parameters['video_note'] = video_note

        if caption is not None:
            parameters['caption'] = caption

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode

        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()

            for param in parameters:
                if param == 'reply_markup':
                    data.add_field(param, json.loads(parameters[param]))
                    continue
                data.add_field(param, str(parameters[param]))

            async with session.post(f'https://api.telegram.org/bot{self.token}/sendVideoNote', data=data) as response:
                try:
                    _msg = Message((await response.json())['result'], self)
                except KeyError:
                    raise Telegram((await response.json())['description'])

        return _msg

    async def send_video(self, chat_id: Union[int, str], video: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        parameters['video'] = video

        if caption is not None:
            parameters['caption'] = caption

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode

        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()

            for param in parameters:
                if param == 'reply_markup':
                    data.add_field(param, json.loads(parameters[param]))
                    continue
                data.add_field(param, str(parameters[param]))

            async with session.post(f'https://api.telegram.org/bot{self.token}/sendVideo', data=data) as response:
                try:
                    _msg = Message((await response.json())['result'], self)
                except KeyError:
                    raise Telegram((await response.json())['description'])

        return _msg

    async def send_paid_media(self, chat_id: Union[int, str], paid_media: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        parameters['paid_media'] = paid_media.file

        if caption is not None:
            parameters['caption'] = caption

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode

        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()

            for param in parameters:
                if param == 'reply_markup':
                    data.add_field(param, json.loads(parameters[param]))
                    continue
                data.add_field(param, str(parameters[param]))

            async with session.post(f'https://api.telegram.org/bot{self.token}/sendPaidMedia', data=data) as response:
                try:
                    _msg = Message((await response.json())['result'], self)
                except KeyError:
                    raise Telegram((await response.json())['description'])

        return _msg

    async def send_contact(self, chat_id: Union[int, str], number: Union[InputFile], first_name: str, last_name: str=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id,
            "first_name": first_name
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        parameters['number'] = number

        if last_name is not None: parameters['last_name'] = last_name

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}

        async with session.post(f'https://api.telegram.org/bot{self.token}/sendContact', json=parameters) as response:
            try:
                _msg = Message((await response.json())['result'], self)
            except KeyError:
                raise Telegram((await response.json())['description'])

        return _msg

    async def send_dice(self, chat_id: Union[int, str], emoji: str, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        if emoji not in ['🎲', '🎯', '🏀', '⚽', '🎳', '🎰']:
            raise TypeError(f'Такой эмодзи {emoji} не допускается.')

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}

        async with session.post(f'https://api.telegram.org/bot{self.token}/sendDice', json=parameters) as response:
            try:
                _msg = Message((await response.json())['result'], self)
            except KeyError:
                raise Telegram((await response.json())['description'])

        return _msg

    async def send_chat_action(self, chat_id: Union[int, str], action: Union[str, ChatAction]):
        parameters = {
            "chat_id": chat_id,
            "action": action
        }

        async with session.post(f'https://api.telegram.org/bot{self.token}/sendChatAction', json=parameters) as response:
            try:
                _msg = Message((await response.json())['result'], self)
            except KeyError:
                raise Telegram((await response.json())['description'])

        return _msg
    
    async def next_step_handler(self, chat_id: int, callback: Callable, *args):
        self._next_step_handlers.append((str(chat_id), callback, args))

    async def polling(self, on_startup: Callable=None, threaded_run: bool=False, thread_max_works: int=10, __imitation=False, *args) -> None:
        """
        Запускает процесс опроса событий, выполняя указанную функцию при старте.

        :param on_startup: Функция, которая будет вызвана при запуске опроса (например, для инициализации).
        :param args: Дополнительные аргументы, которые будут переданы в функцию on_startup.
        :param threaded_run: Запуск с потоком.
        :param thread_max_works: Ограничения по потокам(!Чем больше потоков запустится, тем сильнее нагружается процессор!)
        :return: Ничего не возвращает.
        """

        if on_startup is not None:  asyncio.run(on_startup(args))

        if threaded_run:
            executor = ThreadPoolExecutor(thread_max_works)

        while True:
            async with aiohttp.ClientSession() as session:
                updates = await session.get(f'https://api.telegram.org/bot{self.token}/getUpdates', params={"offset": self.offset})

            if updates.status != 200:
                continue

            imit_updates = get_updates() if __imitation else None
            updates = (await updates.json())["result"]
            process_update = updates or imit_updates if __imitation else updates

            for update in process_update:
                print(update)
                try:
                    self.offset = update["update_id"] + 1

                    if update.get('message', False):
                        
                        for indx, step in enumerate(self._next_step_handlers):
                            if str(update['message']['chat']['id']) == step[0]:
                                if threaded_run:
                                    executor.submit(step[1], Message(update['message'], self), *step[2])
                                else:
                                    await step[1](Message(update['message'], self), *step[2])
                                
                                self._next_step_handlers.pop(indx)
                                break
                        
                        for handler_message in self._message_handlers:
                            if handler_message['filters'] is not None and not handler_message['filters'](Message(update['message'], self)):
                                continue

                            if handler_message['commands'] is not None:
                                if isinstance(handler_message['commands'], list):
                                    if not any(update['message']['text'].split()[0] == '/'+command for command in handler_message['commands']):
                                        continue
                                elif isinstance(handler_message['commands'], str):
                                    if not update['message']['text'].split()[0] == '/'+handler_message['commands']:
                                        continue

                            if isinstance(handler_message['content_types'], str):
                                if not update['message'].get(handler_message['content_types'], False) or handler_message['content_types'] == 'any':
                                    continue
                            elif isinstance(handler_message['content_types'], list):
                                if not any(update['message'].get(__type, False) for __type in handler_message['content_types']) or handler_message['content_types'] == 'any':
                                    continue

                            if isinstance(handler_message['allowed_chat_type'], str):
                                if update['message']['chat']['type'] != handler_message['allowed_chat_type']:
                                    continue
                            elif isinstance(handler_message['allowed_chat_type'], (tuple, list)):
                                if not any(update['message']['chat']['type'] == _chat_type for _chat_type in handler_message['allowed_chat_type']):
                                    continue

                            message = Message(update['message'], self)
                            if threaded_run:
                                executor.submit(self._coroutine_run_with_thread, handler_message['func'], message)
                            else:
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
                            if threaded_run:
                                executor.submit(self._coroutine_run_with_thread, callback['func'], callback_query)
                            else:
                                await callback['func'](callback_query)
                except Exception as e:
                    print('te')
                    traceback.print_exc()
        session.close()

    def executor(self, on_startup: Callable=None, threaded_run: bool=False, thread_max_works: int=10, *args) -> None:
        """
        Удобный способ запуска бота.
        :param on_startup: Функция, которая будет вызвана при запуске опроса (например, для инициализации).
        :param args: Дополнительные аргументы, которые будут переданы в функцию on_startup.
        :return: Ничего не возвращает.
        """
        if not threaded_run: asyncio.run(self.polling())
        else:
            asyncio.run(self.polling(threaded_run=True, thread_max_works=thread_max_works))
        if on_startup is not None:  asyncio.run(on_startup(*args))
    def _coroutine_run_with_thread(self, func: Callable, *args):
        try:
            asyncio.run(func(*args))
        except Exception as e:
            traceback.print_exc()