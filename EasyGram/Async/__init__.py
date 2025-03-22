"""
Асинхронная версия
"""

import aiohttp
import requests
from typing import Union, Callable, Optional, BinaryIO, List, Tuple
import traceback

import asyncio

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
    PollOption,
    InputFile,
    ChatAction,
    Poll
)

from ..exception import Telegram

from io import IOBase, BytesIO

import re

from concurrent.futures import ThreadPoolExecutor

import json

from ..state import StatesGroup, State

import logging

__all__ = [
    'ParseMode',
    'Message',
    'ReplyKeyboardMarkup',
    'GetMe',
    'InlineKeyboardMarkup',
    'CallbackQuery',
    'BotCommand',
    'BotCommandScopeDefault',
    'BotCommandScopeChat',
    'BotCommandScopeAllChatAdministrators',
    'BotCommandScopeChatMember',
    'BotCommandScopeAllGroupChats',
    'BotCommandScopeAllPrivateChats',
    'BotCommandScopeChatAdministrators',
    'User',
    'PollOption',
    'InputFile',
    'ChatAction',
    'Poll',
    'AsyncBot'
]

class AsyncBot:
    """
    Класс для управления ботом асинхронно.
    """
    offset = 0
    _message_handlers = []
    _callback_query_handlers = []
    _next_step_handlers = []
    _poll_handlers = []
    _query_next_step_handlers = []

    __session__: aiohttp.ClientSession = aiohttp.ClientSession(connector=aiohttp.TCPConnector(keepalive_timeout=30))

    def __init__(self, token: str, log_level: int=logging.INFO):
        """
        Инициализирует AsyncBot с заданным токеном.

        Args:
            token (str): Токен для аутентификации запросов к API Telegram.
            log_level (int): Уровень логирования.
        """
        self.token = token

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        try:
            response = requests.get(f'https://api.telegram.org/bot{self.token}/getMe').json()
        except (TimeoutError, aiohttp.ClientError, ConnectionError) as e:
            raise ConnectionError('Connection error')
        except Exception as e:
            raise Telegram('The token is incorrectly set.')

        self.logger.debug(f'The bot is launched with user name @{response["result"]["username"]}')

    async def get_me(self) -> User:
        """
        Получает информацию о боте из Telegram.

        Returns:
            User: Объект, представляющий бота.
        """
        response = requests.get(f'https://api.telegram.org/bot{self.token}/getMe')

        return User(response.json()['result'])

    def set_my_commands(self, commands: List[BotCommand], scope: Union[BotCommandScopeChat, BotCommandScopeDefault, BotCommandScopeChatMember, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats, BotCommandScopeChatAdministrators, BotCommandScopeAllChatAdministrators]=None, language_code: str=None) -> bool:
        """
        Устанавливает команды для бота.

        Args:
            commands (List[BotCommand]): Список команд для установки.
            scope (Union[BotCommandScopeChat, BotCommandScopeDefault, etc.], optional): Область видимости команд.
            language_code (str, optional): Код языка для локализации команд.

        Returns:
            bool: Возвращает True, если команды успешно установлены.
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
        Отправляет текстовое сообщение пользователю или в чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата.
            text (Union[int, float, str]): Текст сообщения.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup], optional): Клавиатура для сообщения.
            parse_mode (str, optional): Режим форматирования текста.
            reply_to_message_id (int, optional): Если указан, сообщение будет отправлено как ответ на указанное сообщение.

        Returns:
            Message: Объект сообщения, отправленного ботом.
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

        try:
            async with self.__session__.post(f"https://api.telegram.org/bot{self.token}/sendMessage", json=parameters) as response:
                _msg = Message((await response.json())['result'], self)
        except KeyError:
            _description = await response.json()
            raise Telegram(_description['description'])
        except AttributeError:
            raise ValueError('Бот не запущен.')
        except Exception:
            traceback.print_exc()
            raise Telegram()

        return _msg

    async def send_photo(self, chat_id: Union[int, str], photo: Union[InputFile], caption: Union[int, float, str]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, parse_mode: str=None, photo_name: str=None, reply_to_message_id: int=None):
        """
        Отправляет фотографию в чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата.
            photo (Union[InputFile]): Файл фотографии.
            caption (Union[int, float, str], optional): Подпись к фотографии.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup], optional): Клавиатура для сообщения.
            parse_mode (str, optional): Режим форматирования текста подписи.
            photo_name (str, optional): Имя файла фотографии.
            reply_to_message_id (int, optional): Если указан, сообщение будет отправлено как ответ на указанное сообщение.

        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
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

        data = aiohttp.FormData()

        for param in parameters:
            if param == 'reply_markup':
                data.add_field(param, json.dumps(parameters[param]))
                continue
            data.add_field(param, str(parameters[param]))

        data.add_field('photo', photo.file, filename=name, content_type=f'image/{_type}')

        try:
            async with self.__session__.post(f"https://api.telegram.org/bot{self.token}/sendPhoto", data=data) as response:
                _msg = Message((await response.json())['result'], self)
        except KeyError:
            raise Telegram((await response.json())['description'])
        except AttributeError:
            raise ValueError('Бот не запущен')
        except Exception:
            traceback.print_exc()
            raise Telegram()

        return _msg

    def message(self, _filters: Callable[[Message], any]=None, content_types: Union[str, List[str]]=None, commands: Union[str, List[str]]=None, allowed_chat_type: Union[List[str], Tuple[str], str]=None, state: State=None) -> Callable:
        """
        Декоратор для обработки входящих сообщений.

        Args:
            _filters (Callable[[Message], any], optional): Функция фильтрации сообщений.
            content_types (Union[str, List[str]], optional): Типы контента, которые должен обрабатывать обработчик.
            commands (Union[str, List[str]], optional): Команды, на которые должен реагировать обработчик.
            allowed_chat_type (Union[List[str], Tuple[str], str], optional): Типы чатов, в которых активен обработчик.
            state (StateRegExp, optional): Состояние в контексте машины состояний.

        Returns:
            Callable: Функция-обертка, которая регистрирует обработчик сообщений.
        """
        def wrapper(func):
            self._message_handlers.append({'func': func, 'filters': _filters, 'content_types': content_types, 'commands': commands, 'allowed_chat_type': allowed_chat_type, 'state': state})
        return wrapper

    def message_handler(self, _filters: Callable[[Message], any]=None, content_types: Union[str, List[str]]=None, commands: Union[str, List[str]]=None, allowed_chat_type: Union[List[str], Tuple[str], str]=None, state: State=None) -> Callable:
        """
        Декоратор для обработки входящих сообщений, предназначенный для миграции из aiogram2 в EasyGram.

        Args:
            _filters (Callable[[Message], any], optional): Функция фильтрации сообщений.
            content_types (Union[str, List[str]], optional): Типы контента, которые должен обрабатывать обработчик.
            commands (Union[str, List[str]], optional): Команды, на которые должен реагировать обработчик.
            allowed_chat_type (Union[List[str], Tuple[str], str], optional): Типы чатов, в которых активен обработчик.
            state (StateRegExp, optional): Состояние в контексте машины состояний.

        Returns:
            Callable: Функция-обертка, которая регистрирует обработчик сообщений.
        """
        def wrapper(func):
            self._message_handlers.append({'func': func, 'filters': _filters, 'content_types': content_types, 'commands': commands, 'allowed_chat_type': allowed_chat_type, 'state': state})
        return wrapper

    def callback_query(self, _filters: Callable[[CallbackQuery], any]=None, allowed_chat_type: Union[str, List[str], Tuple[str]]=None, state: State=None) -> Callable:
        """
        Декоратор для обработки callback-запросов от InlineKeyboardMarkup.

        Args:
            _filters (Callable[[CallbackQuery], any], optional): Функция фильтрации запросов.
            allowed_chat_type (Union[str, List[str], Tuple[str]], optional): Типы чатов, в которых активен обработчик.
            state (StateRegExp, optional): Состояние в контексте машины состояний.

        Returns:
            Callable: Функция-обертка, которая регистрирует обработчик запросов.
        """
        def wrapper(func):
            self._callback_query_handlers.append({'func': func, 'filters': _filters, 'allowed_chat_type': allowed_chat_type, 'state': state})
        return wrapper

    def callback_query_handler(self, _filters: Callable[[CallbackQuery], any]=None, allowed_chat_type: Union[str, List[str], Tuple[str]]=None, state: State=None) -> Callable:
        """
        Декоратор для обработки callback-запросов от InlineKeyboardMarkup, предназначенный для миграции из aiogram2 в EasyGram.

        Args:
            _filters (Callable[[CallbackQuery], any], optional): Функция фильтрации запросов.
            allowed_chat_type (Union[str, List[str], Tuple[str]], optional): Типы чатов, в которых активен обработчик.
            state (StateRegExp, optional): Состояние в контексте машины состояний.

        Returns:
            Callable: Функция-обертка, которая регистрирует обработчик запросов.
        """
        def wrapper(func):
            self._callback_query_handlers.append({'func': func, 'filters': _filters, 'allowed_chat_type': allowed_chat_type, 'state': state})
        return wrapper
    
    def poll_handler(self, _filters: Callable[[Poll], any]=None, allowed_chat_type: Union[str, List[str], Tuple[str]]=None, state: State=None) -> None:
        """
        Декоратор для обработки опросов, предназначенный для миграции из pyTelegramBotAPI в EasyGram.

        Args:
            _filters (Callable[[Poll], any], optional): Функция фильтрации опросов.
            allowed_chat_type (Union[str, List[str], Tuple[str]], optional): Типы чатов, в которых активен обработчик.
            state (StateRegExp, optional): Состояние в контексте машины состояний.
        """

        def wrapper(func):
            self._poll_handlers.append({'func': func, 'filters': _filters, 'allowed_chat_type': allowed_chat_type, 'state': state})
        return wrapper
    
    def poll(self, _filters: Callable[[Poll], any]=None, allowed_chat_type: Union[str, List[str], Tuple[str]]=None, state: State=None) -> None:
        """
        Декоратор для обработки опросов, предназначенный для миграции из pyTelegramBotAPI в EasyGram.

        Args:
            _filters (Callable[[Poll], any], optional): Функция фильтрации опросов.
            allowed_chat_type (Union[str, List[str], Tuple[str]], optional): Типы чатов, в которых активен обработчик.
            state (StateRegExp, optional): Состояние в контексте машины состояний.
        """

        def wrapper(func):
            self._poll_handlers.append({'func': func, 'filters': _filters, 'allowed_chat_type': allowed_chat_type, 'state': state})
        return wrapper

    async def answer_callback_query(self, chat_id: Union[int, str], text: Union[int, float, str]=None, show_alert: bool=False) -> bool:
        """
        Отправляет ответ на callback-запрос пользователя.

        Args:
            chat_id (Union[int, str]): Идентификатор чата.
            text (Union[int, float, str], optional): Текст ответа.
            show_alert (bool, optional): Если True, ответ будет показан в виде всплывающего уведомления.

        Returns:
            bool: Возвращает True, если ответ был успешно отправлен.
        """
        parameters = {
            'callback_query_id': chat_id,
            'text': str(text),
            'show_alert': show_alert
        }
        
        try:
            async with self.__session__.post(f"https://api.telegram.org/bot{self.token}/answerCallbackQuery", json=parameters) as response:
                _msg = (await response.json())['result']
        except KeyError:
            raise Telegram((await response.json())['description'])
        except AttributeError:
            raise ValueError('Бот не запущен')
        except Exception:
            traceback.print_exc()
            raise Telegram()

        return _msg

    async def delete_message(self, chat_id: Union[int, str], message_id: int) -> bool:
        """
        Удаляет сообщение из чата.
        - Сообщение можно удалить, только если оно было отправлено менее 48 часов назад.
        - Сообщение в приватном чате можно удалить, только если оно было отправлено более 24 часов назад.

        Args:
            chat_id (Union[int, str]): Идентификатор чата.
            message_id (int): Идентификатор сообщения для удаления.

        Returns:
            bool: Возвращает True, если сообщение было успешно удалено.
        """
        parameters = {
            'chat_id': chat_id,
            'message_id': message_id
        }

        try:
            async with self.__session__.post(f"https://api.telegram.org/bot{self.token}/deleteMessage", json=parameters) as response:
                _msg = (await response.json())['result']
        except KeyError:
            raise Telegram((await response.json())['description'])
        except AttributeError:
            raise ValueError('Бот не запущен')
        except Exception:
            traceback.print_exc()
            raise Telegram()

        return _msg

    async def edit_message_text(self, chat_id: Union[int, str], message_id: int, text: Union[int, float, str], parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None) -> bool:
        """
        Редактирует текст существующего сообщения.
        - Обратите внимание, что деловые сообщения, которые не были отправлены ботом и не содержат встроенной клавиатуры, можно редактировать только в течение 48 часов с момента отправки.

        Args:
            chat_id (Union[int, str]): Идентификатор чата.
            message_id (int): Идентификатор редактируемого сообщения.
            text (Union[int, float, str]): Новый текст сообщения.
            parse_mode (Union[str, ParseMode], optional): Режим форматирования текста.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup], optional): Клавиатура для сообщения.

        Returns:
            bool: Возвращает True, если сообщение было успешно отредактировано.
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

        try:
            async with self.__session__.post(f"https://api.telegram.org/bot{self.token}/editMessageText", json=parameters) as response:
                _msg = (await response.json())['result']
        except KeyError:
            raise Telegram((await response.json())['description'])
        except AttributeError:
            raise ValueError('Бот не запущен')
        except Exception:
            traceback.print_exc()
            raise Telegram()

        return _msg

    async def send_poll(self, chat_id: Union[int, str], question: Union[int, float, str], options: Union[List[PollOption], List[str]], question_parse_mode: Union[str, ParseMode]=None, is_anonymous: bool=True, type: str='regular', allows_multiple_answers: bool=False, correct_option_id: int=0, explanation: str=None, explanation_parse_mode: Union[str, ParseMode]=None, open_period: int=None, is_closed: bool=False, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправляет опрос в указанный чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата, в который отправляется опрос.
            question (Union[int, float, str]): Текст вопроса опроса.
            options (Union[List[PollOption], List[str]]): Список вариантов ответов.
            question_parse_mode (Union[str, ParseMode], optional): Режим форматирования текста вопроса.
            is_anonymous (bool, optional): Указывает, является ли опрос анонимным.
            type (str, optional): Тип опроса ('regular' или 'quiz').
            allows_multiple_answers (bool, optional): Разрешить ли выбор нескольких вариантов ответов.
            correct_option_id (int, optional): Индекс правильного ответа, если опрос является викториной.
            explanation (str, optional): Объяснение, которое следует после опроса.
            explanation_parse_mode (Union[str, ParseMode], optional): Режим форматирования текста объяснения.
            open_period (int, optional): Время в секундах, в течение которого опрос будет активен.
            is_closed (bool, optional): Закрыть ли опрос сразу после создания.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup], optional): Клавиатура, которая будет отображаться с сообщением.
            reply_to_message_id (int, optional): Идентификатор сообщения, на которое должен ответить опрос.

        Returns:
            Message: Объект сообщения, содержащий опрос.
        """
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
        elif len(options) > 10:
            try:
                raise Telegram('В списке параметра options должно быть максимум 10 элементов.')
            except Telegram as e:
                traceback.print_exc(e)
        else:
            parameters['options'] = []
            for option in options:
                if isinstance(option, PollOption):
                    _opt = {"text": option.text}
                    if option.text_parse_mode is not None: _opt.update({"text_parse_mode": option.text_parse_mode})
                    parameters['options'].append(_opt)
                else:
                    parameters['options'].append({"text": option})

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
        
        try:
            async with self.__session__.post(f"https://api.telegram.org/bot{self.token}/sendPoll", json=parameters) as response:
                _msg = Message((await response.json())['result'], self)
        except KeyError:
            raise Telegram((await response.json())['description'])
        except AttributeError:
            raise ValueError('Бот не запущен')
        except Exception:
            traceback.print_exc()
            raise Telegram()

        return _msg

    async def send_audio(self, chat_id: Union[int, str], audio: Union[InputFile], title: str=None, caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправляет аудиофайл в указанный чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата, в который отправляется аудио.
            audio (Union[InputFile]): Аудиофайл для отправки.
            title (str, optional): Название аудиофайла.
            caption (str, optional): Подпись к аудиофайлу.
            parse_mode (Union[str, ParseMode], optional): Режим форматирования текста подписи.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup], optional): Клавиатура для сообщения.
            reply_to_message_id (int, optional): Идентификатор сообщения, на которое должен быть дан ответ.

        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
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

        data = aiohttp.FormData()

        for param in parameters:
            if param == 'reply_markup':
                data.add_field(param, json.loads(parameters[param]))
                continue
            data.add_field(param, str(parameters[param]))

        try:
            async with self.__session__.post(f'https://api.telegram.org/bot{self.token}/sendAudio', data=data) as response:
                _msg = Message((await response.json())['result'], self)
        except KeyError:
            raise Telegram((await response.json())['description'])
        except AttributeError:
            raise ValueError('Бот не запущен')
        except Exception:
            traceback.print_exc()
            raise Telegram()

        return _msg

    async def send_document(self, chat_id: Union[int, str], document: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправляет документ в указанный чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата, в который отправляется документ.
            document (Union[InputFile]): Файл документа для отправки.
            caption (str, optional): Подпись к документу.
            parse_mode (Union[str, ParseMode], optional): Режим форматирования текста подписи.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup], optional): Клавиатура, прикрепляемая к сообщению.
            reply_to_message_id (int, optional): Идентификатор сообщения, на которое должен быть дан ответ.

        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
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

        data = aiohttp.FormData()

        for param in parameters:
            if param == 'reply_markup':
                data.add_field(param, json.loads(parameters[param]))
                continue
            data.add_field(param, str(parameters[param]))
        
        try:
            async with self.__session__.post(f'https://api.telegram.org/bot{self.token}/sendDocument', data=data) as response:
                _msg = Message((await response.json())['result'], self)
        except KeyError:
            raise Telegram((await response.json())['description'])
        except AttributeError:
            raise ValueError('Бот не запущен')
        except Exception:
            traceback.print_exc()
            raise Telegram()

        return _msg

    async def send_animation(self, chat_id: Union[int, str], animation: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправляет анимацию (видео или GIF) в указанный чат.
        
        Args:
            chat_id (Union[int, str]): Идентификатор чата, в который отправляется анимация.
            animation (Union[InputFile]): Файл анимации для отправки.
            caption (str, optional): Подпись к анимации.
            parse_mode (Union[str, ParseMode], optional): Режим форматирования текста подписи.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup], optional): Клавиатура, прикрепляемая к сообщению.
            reply_to_message_id (int, optional): Идентификатор сообщения, на которое должен быть дан ответ.
        
        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
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

        data = aiohttp.FormData()

        for param in parameters:
            if param == 'reply_markup':
                data.add_field(param, json.loads(parameters[param]))
                continue
            data.add_field(param, str(parameters[param]))
        
        try:
            async with self.__session__.post(f'https://api.telegram.org/bot{self.token}/sendDocument', data=data) as response:
                _msg = Message((await response.json())['result'], self)
        except KeyError:
            raise Telegram((await response.json())['description'])
        except AttributeError:
            raise ValueError('Бот не запущен')
        except Exception:
            traceback.print_exc()
            raise Telegram()

        return _msg

    async def send_voice(self, chat_id: Union[int, str], voice: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправляет голосовое сообщение в указанный чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата, в который отправляется сообщение.
            voice (Union[InputFile]): Файл голосового сообщения для отправки.
            caption (str, optional): Подпись к голосовому сообщению.
            parse_mode (Union[str, ParseMode], optional): Режим форматирования текста подписи.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup], optional): Клавиатура, прикрепляемая к сообщению.
            reply_to_message_id (int, optional): Идентификатор сообщения, на которое должен быть дан ответ.

        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
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
        """
        Отправляет видеозаметку в указанный чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата, в который отправляется видеозаметка.
            video_note (Union[InputFile]): Файл видеозаметки для отправки.
            caption (str, optional): Подпись к видеозаметке.
            parse_mode (Union[str, ParseMode], optional): Режим форматирования текста подписи.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup], optional): Клавиатура, прикрепляемая к сообщению.
            reply_to_message_id (int, optional): Идентификатор сообщения, на которое должен быть дан ответ.

        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
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
        """
        Отправляет видео в указанный чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата, в который отправляется видео.
            video (Union[InputFile]): Файл видео для отправки.
            caption (str, optional): Подпись к видео.
            parse_mode (Union[str, ParseMode], optional): Режим форматирования текста подписи.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup], optional): Клавиатура, прикрепляемая к сообщению.
            reply_to_message_id (int, optional): Идентификатор сообщения, на которое должен быть дан ответ.

        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
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

    async def send_contact(self, chat_id: Union[int, str], number: Union[InputFile], first_name: str, last_name: str=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправляет контакт в указанный чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата, в который отправляется контакт.
            number (Union[InputFile]): Номер телефона контакта.
            first_name (str): Имя контакта.
            last_name (str, optional): Фамилия контакта.
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup], optional): Клавиатура, прикрепляемая к сообщению.
            reply_to_message_id (int, optional): Идентификатор сообщения, на которое должен быть дан ответ.

        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
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

        async with aiohttp.ClientSession() as session:
            async with session.post(f'https://api.telegram.org/bot{self.token}/sendContact', json=parameters) as response:
                try:
                    _msg = Message((await response.json())['result'], self)
                except KeyError:
                    raise Telegram((await response.json())['description'])

        return _msg

    async def send_dice(self, chat_id: Union[int, str], emoji: str, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправляет анимированный эмодзи в чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата.
            emoji (str): Эмодзи для отправки (допустимые значения: 🎲, 🎯, 🏀, ⚽, 🎳, 🎰).
            reply_markup (Union[ReplyKeyboardMarkup, InlineKeyboardMarkup], optional): Клавиатура для сообщения.
            reply_to_message_id (int, optional): ID сообщения, на которое должен быть дан ответ.

        Returns:
            Message: Объект сообщения, отправленного ботом.
        """
        parameters = {
            "chat_id": chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        if emoji not in ['🎲', '🎯', '🏀', '⚽', '🎳', '🎰']:
            raise TypeError(f'Эмодзи {emoji} не поддерживается.')

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}

        async with aiohttp.ClientSession() as session:
            async with session.post(f'https://api.telegram.org/bot{self.token}/sendDice', json=parameters) as response:
                try:
                    _msg = Message((await response.json())['result'], self)
                except KeyError:
                    raise Telegram((await response.json())['description'])

        return _msg

    async def send_chat_action(self, chat_id: Union[int, str], action: Union[str, ChatAction]) -> None:
        """
        Отправляет статус действия в чат.

        Args:
            chat_id (Union[int, str]): Идентификатор чата.
            action (Union[str, ChatAction]): Тип действия (см. EasyGram.types.ChatAction/EasyGram.Async.types.ChatAction).

        Returns:
            None
        """
        parameters = {
            "chat_id": chat_id,
            "action": action
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(f'https://api.telegram.org/bot{self.token}/sendChatAction', json=parameters) as response:
                try:
                    _msg = Message((await response.json())['result'], self)
                except KeyError:
                    raise Telegram((await response.json())['description'])
    
    async def next_step_handler(self, chat_id: int, callback: Callable, *args):
        """
        Устанавливает обработчик следующего шага для сообщений от пользователя.

        Args:
            chat_id (int): Идентификатор чата.
            callback (Callable): Функция обратного вызова, которая будет вызвана при получении сообщения.
            args: Аргументы, передаваемые в функцию обратного вызова.

        Returns:
            None
        """
        self._next_step_handlers.append((str(chat_id), callback, args))
    
    async def query_next_step_handler(self, chat_id: int, callback: Callable, *args):
        """
        Устанавливает обработчик следующего шага для inline-запросов от пользователя.

        Args:
            chat_id (int): Идентификатор чата.
            callback (Callable): Функция обратного вызова, которая будет вызвана при нажатии на inline-кнопку.
            args: Аргументы, передаваемые в функцию обратного вызова.

        Returns:
            None
        """
        self._query_next_step_handlers.append((str(chat_id), callback, args))

    async def polling(self, on_startup: Callable=None, threaded_run: bool=False, thread_max_works: int=10, *args) -> None:
        """
        Запускает процесс опроса сервера Telegram для получения обновлений.

        Args:
            on_startup (Callable, optional): Функция, вызываемая при запуске опроса.
            threaded_run (bool, optional): Если True, опрос выполняется в отдельных потоках.
            thread_max_works (int, optional): Максимальное количество потоков.
            args: Дополнительные аргументы, передаваемые в функцию on_startup.

        Returns:
            None
        """

        if on_startup is not None:  asyncio.run(on_startup(args))

        if threaded_run:
            executor = ThreadPoolExecutor(thread_max_works)

        try:
                while True:
                    async with self.__session__.get(f'https://api.telegram.org/bot{self.token}/getUpdates', params={"offset": self.offset, "timeout": 30, "allowed_updates": ["message", "callback_query", "poll"]}, timeout=35) as response:
                        if response.status != 200:
                            continue
                        
                        updates = response

                        updates = (await updates.json())["result"]

                    for update in updates:
                        self.offset = update["update_id"] + 1

                        if update.get('message', False):
                            
                            for indx, step in enumerate(self._next_step_handlers):
                                if str(update['message']['chat']['id']) == step[0]:
                                    if threaded_run:
                                        executor.submit(self._coroutine_run_with_thread, step[1], Message(update['message'], self), *step[2])
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

                                if handler_message['state'] is not None:
                                    if update['message']['from']['id'] not in StatesGroup.user_registers:
                                        continue

                                    if handler_message['state'] != StatesGroup.user_registers[update['message']['from']['id']]['state']:
                                        continue

                                message = Message(update['message'], self)
                            parameters = [message]
                            parameters.append(FSMContext(message.from_user.id))
                            
                            is_method = inspect.ismethod(handler_message['func'])
                            _parameters = list(inspect.signature(handler_message['func']).parameters)

                            if is_method and len(_parameters) > 0: _parameters.pop(0)

                            if len(_parameters) == 1: parameters.pop(1)

                            if threaded_run:
                                executor.submit(self._coroutine_run_with_thread, handler_message['func'], *parameters)
                            else:
                                await handler_message['func'](*parameters)
                                
                            break
                        elif update.get('callback_query', False):
                            for indx, step in enumerate(self._query_next_step_handlers):
                                if str(update['callback_query']['message']['chat']['id']) == step[0]:
                                    if threaded_run:
                                        executor.submit(self._coroutine_run_with_thread, step[1], CallbackQuery(update['callback_query'], self), *step[2])
                                    else:
                                        await step[1](CallbackQuery(update['callback_query'], self), *step[2])
                                    
                                    self._query_next_step_handlers.pop(indx)
                                    break

                            for callback in self._callback_query_handlers:
                                if callback['filters'] is not None and not callback['filters'](CallbackQuery(update['callback_query'], self)):
                                    continue

                                if isinstance(callback['allowed_chat_type'], str):
                                    if update['callback_query']['chat']['type'] != callback['allowed_chat_type']:
                                        continue
                                elif isinstance(callback['allowed_chat_type'], (tuple, list)):
                                    if not any(update['callback_query']['chat']['type'] == _chat_type for _chat_type in callback['allowed_chat_type']):
                                        continue

                                if callback['state'] is not None:
                                    if update['message']['from']['id'] not in StatesGroup.user_registers:
                                        continue

                                    if callback['state'] != StatesGroup.user_registers[update['message']['from']['id']]['state']:
                                        continue
                                
                                callback_query = CallbackQuery(update['callback_query'], self)
                            parameters = [callback_query]
                            parameters.append(FSMContext(callback_query.from_user.id))

                            is_method = inspect.ismethod(callback['func'])
                            _parameters = list(inspect.signature(callback['func']).parameters)

                            if is_method and len(_parameters) > 0: _parameters.pop(0)

                            if len(_parameters) == 1: parameters.pop(1)

                            if threaded_run:
                                executor.submit(self._coroutine_run_with_thread, callback['func'], *parameters)
                            else:
                                await callback['func'](*parameters)
                            
                            break
                        elif update.get('poll', False):
                            for poll in self._poll_handlers:
                                if poll['filters'] is not None and not poll['filters'](Poll(update['poll'])):
                                    continue

                                if isinstance(poll['allowed_chat_type'], list):
                                    if not any(_chat_type == update['poll']['chat']['type'] for _chat_type in poll['allowed_chat_type']):
                                        continue
                                elif isinstance(poll['allowed_chat_type'], str):
                                    if update['poll']['chat']['type'] != poll['allowed_chat_type']:
                                        continue
                                
                                if poll['state'] is not None:
                                    if update['message']['from']['id'] not in StatesGroup.user_registers:
                                        continue

                                    if poll['state'] != StatesGroup.user_registers[update['message']['from']['id']]['state']:
                                        continue
                                
                                _poll = Poll(update['poll'])

                                if threaded_run:
                                    executor.submit(poll['func'], _poll)
                                else:
                                    poll['func'](_poll)
                                
                                break
        except Exception as e:
            self.logger.error(traceback.format_exc())

    def executor(self, on_startup: Callable=None, threaded_run: bool=False, thread_max_works: int=10, *args) -> None:
        """
        Запускает бота с возможностью использования многопоточности.

        Args:
            on_startup (Callable, optional): Функция, вызываемая при запуске.
            threaded_run (bool, optional): Если True, используется многопоточность.
            thread_max_works (int, optional): Максимальное количество потоков.
            args: Дополнительные аргументы.

        Returns:
            None
        """
        
        if on_startup is not None: asyncio.run(on_startup)

        if not threaded_run: asyncio.run(self.polling())
        else:
            with ThreadPoolExecutor(thread_max_works) as executor:
                executor.submit(self._coroutine_run_with_thread, self.polling, *args)
    def _coroutine_run_with_thread(self, func: Callable, *args):
        try:
            asyncio.run(func(*args))
        except Exception as e:
            traceback.print_exc()