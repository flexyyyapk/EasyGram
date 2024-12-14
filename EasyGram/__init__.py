__name__ = 'EasyGram'
__version__ = '0.0.2'

from io import IOBase, BytesIO

import requests
from typing import Union, Callable, Optional, BinaryIO, List, Tuple
import traceback

from .types import (
    Message,
    GetMe,
    ReplyKeyboardMarkup,
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
    ParseMode,
    InputPollOption,
    InputFile,
    ChatAction
)

from .exception import Telegram

from concurrent.futures import ThreadPoolExecutor

import traceback

from random import randint

class SyncBot:
    offset = 0
    _message_handlers = []
    _callback_query_handlers = []
    _next_step_handlers = []

    def __init__(self, token: str):
        self.token = token

    def get_me(self) -> GetMe:
        """
        Информация о боте.
        :return: GetMe object
        """
        return GetMe(self)

    def set_my_commands(self, commands: List[BotCommand], scope: Union[BotCommandScopeChat, BotCommandScopeDefault, BotCommandScopeChatMember, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats, BotCommandScopeChatAdministrators, BotCommandScopeAllChatAdministrators]=None, language_code: str=None) -> bool:
        """
        Установка команд в меню команд.
        :param commands: команды
        :param scope: в каком окружении установится команды
        :param language_code: языковой код
        :return: True or False
        """
        parameters = {
            'commands': commands
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

        if not response.json()['ok']:
            raise Telegram(response.json()['description'])

        return bool(response.json()['result'])

    def send_message(self, chat_id: Union[int, str], text: Union[int, float, str], reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, parse_mode: Union[str, ParseMode]=None, reply_to_message_id: int=None) -> Message:
        """
        Отправка сообщений.
        :param chat_id: Айди чата
        :param text: Текст
        :param reply_markup: Кнопки ReplyKeyboardMarkup или InlineKeyboardMarkup
        :param parse_mode: Форматирования текста
        :param reply_to_message_id: Ответ на сообщение
        :return: Message
        """
        parameters = {
            'chat_id': chat_id,
            'text': text
        }

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}

        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        response = requests.post(f"https://api.telegram.org/bot{self.token}/sendMessage", json=parameters)

        if response.json()['ok'] == False:
            raise Telegram(response.json()['description'])

        return Message(response.json()['result'], self)

    def send_photo(self, chat_id: Union[int, str], photo: Union[InputFile], caption: Union[int, float, str]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, parse_mode: Union[str, ParseMode]=None, reply_to_message_id: int=None):
        parameters = {
            "chat_id": chat_id
        }

        files = {}

        files['photo'] = photo.file

        if caption is not None:
            parameters['caption'] = caption

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
            
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        response = requests.post(f"https://api.telegram.org/bot{self.token}/sendPhoto", data=parameters, files=files)

        if response.json()['ok'] == False:
            raise Telegram(response.json()['description'])

        return Message(response.json()['result'], self)

    def message(self, _filters: Callable=None, content_types: Union[str, List[str]]=None, commands: Union[str, List[str]]=None, allowed_chat_type: Union[str, List[str], Tuple[str]]=None) -> Callable:
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

    def message_handler(self, _filters: Callable=None, content_types: Union[str, List[str]]=None, commands: Union[str, List[str]]=None, allowed_chat_type: Union[str, List[str], Tuple[str]]=None) -> Callable:
        """
        Декоратор для обработки входящих сообщений.Для миграции из pyTelegramBotAPI в EasyGram
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
        Декоратор для обработки вызовов InlineKeyboardMarkup кнопки.Для миграции из pyTelegramBotAPI в EasyGram
        :param _filters: лямбда
        :param allowed_chat_type: тип группы
        :return: Функцию которую нужно вызвать
        """
        def wrapper(func):
            self._callback_query_handlers.append({'func': func, 'filters': _filters, 'allowed_chat_type': allowed_chat_type})
        return wrapper

    def answer_callback_query(self, query_id: Union[int, str], text: Union[int, float, str]=None, show_alert: bool=False) -> bool:
        """
        Отправляет ответ на callback-запрос от пользователя.
        :param chat_id: Идентификатор чата, может быть целым числом или строкой.
        :param text: Текст сообщения, который будет показан пользователю в ответ на callback-запрос.
        :param show_alert: Если True, сообщение будет отображаться в виде всплывающего окна (alert).
        :return: Возвращает True, если запрос был успешным, иначе False.
        """
        parameters = {
            'callback_query_id': query_id,
            'text': str(text),
            'show_alert': show_alert
        }

        response = requests.post(f"https://api.telegram.org/bot{self.token}/answerCallbackQuery", json=parameters)

        if response.json()['ok'] == False:
            raise Telegram(response.json()['description'])

        return response.json()['result']

    def delete_message(self, chat_id: Union[int, str], message_id: int) -> bool:
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

        response = requests.post(f"https://api.telegram.org/bot{self.token}/deleteMessage", json=parameters)

        if not response.json()['ok']:
            raise Telegram(response.json()['description'])

        return response.json()['result']

    def edit_message_text(self, chat_id: Union[int, str], message_id: int, text: Union[int, float, str], parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None) -> bool:
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
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}

        response = requests.post(f"https://api.telegram.org/bot{self.token}/editMessageText", json=parameters)

        if not response.json()['ok']:
            raise Telegram(response.json()['description'])

        return response.json()['result']

    def send_poll(self, chat_id: Union[int, str], question: Union[int, float, str], options: Union[List[InputPollOption], List[str]], question_parse_mode: Union[str, ParseMode]=None, is_anonymous: bool=True, type: str='regular', allows_multiple_answers: bool=False, correct_option_id: int=0, explanation: str=None, explanation_parse_mode: Union[str, ParseMode]=None, open_period: int=None, is_closed: bool=False, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id,
            "question": str(question),
            "type": type,
            "allows_multiple_answers": allows_multiple_answers,
            "is_closed": is_closed
        }

        if len(options) < 2:
            try:
                raise Telegram('В списке параметра options должно быть минимум 2 элемента.')
            except Telegram as e:
                traceback.print_exc(e)
        else:
            parameters['options'] = []
            for option in options:
                if isinstance(option, InputPollOption):
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
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}

        if open_period is not None:
            parameters['open_period'] = open_period
            
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        response = requests.post(f"https://api.telegram.org/bot{self.token}/sendPoll", json=parameters)

        if not response.json()['ok']:
            raise Telegram(response.json()['description'])

        return Message(response.json()['result'], self)

    def send_audio(self, chat_id: Union[int, str], audio: Union[InputFile], title: str=None, caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id
        }

        files = {

        }

        if isinstance(audio, str):
            with open(audio, 'rb') as f:
                files['audio'] = f
                parameters['title'] = f.name if title is None else title
        else:
            files['audio'] = audio
            parameters['title'] = 'audio' if title is None else title

        if caption is not None:
            parameters['caption'] = caption

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
            
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        response = requests.post(f'https://api.telegram.org/bot{self.token}/sendAudio', data=parameters, files=files)

        if not response.json()['ok']:
            raise Telegram(response.json()['description'])

        return Message(response.json()['result'], self)

    def send_document(self, chat_id: Union[int, str], document: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id
        }

        files = {

        }

        files['document'] = document.file

        if caption is not None:
            parameters['caption'] = caption

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
            
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        response = requests.post(f'https://api.telegram.org/bot{self.token}/sendDocument', data=parameters, files=files)

        if not response.json()['ok']:
            raise Telegram(response.json()['description'])

        return Message(response.json()['result'], self)

    def send_animation(self, chat_id: Union[int, str], animation: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id
        }

        files = {

        }

        files['animation'] = animation.file

        if caption is not None:
            parameters['caption'] = caption

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
            
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        response = requests.post(f'https://api.telegram.org/bot{self.token}/sendAnimation', data=parameters, files=files)

        if not response.json()['ok']:
            raise Telegram(response.json()['description'])

        return Message(response.json()['result'], self)

    def send_voice(self, chat_id: Union[int, str], voice: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id
        }

        files = {

        }

        files['voice'] = voice.file

        if caption is not None:
            parameters['caption'] = caption

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
            
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        response = requests.post(f'https://api.telegram.org/bot{self.token}/sendVoice', data=parameters, files=files)

        if not response.json()['ok']:
            raise Telegram(response.json()['description'])

        return Message(response.json()['result'], self)

    def send_video(self, chat_id: Union[int, str], video: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id
        }

        files = {

        }

        files['video'] = video.file

        if caption is not None:
            parameters['caption'] = caption

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
            
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        response = requests.post(f'https://api.telegram.org/bot{self.token}/sendVideo', data=parameters, files=files)

        if not response.json()['ok']:
            raise Telegram(response.json()['description'])

        return Message(response.json()['result'], self)

    def send_video_note(self, chat_id: Union[int, str], video_note: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id
        }

        files = {

        }

        files['video_note'] = video_note.file

        if caption is not None:
            parameters['caption'] = caption

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
            
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        response = requests.post(f'https://api.telegram.org/bot{self.token}/sendVideoNote', data=parameters, files=files)

        if not response.json()['ok']:
            raise Telegram(response.json()['description'])

        return Message(response.json()['result'], self)

    def send_paid_media(self, chat_id: Union[int, str], paid_media: Union[InputFile], caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id
        }

        files = {

        }

        files['paid_media'] = paid_media.file

        if caption is not None:
            parameters['caption'] = caption

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}
        if parse_mode is not None:
            parameters['parse_mode'] = parse_mode
            
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        response = requests.post(f'https://api.telegram.org/bot{self.token}/sendPaidMedia', data=parameters, files=files)

        if not response.json()['ok']:
            raise Telegram(response.json()['description'])

        return Message(response.json()['result'], self)

    def send_contact(self, chat_id: Union[int, str], number: str, first_name: str, last_name: str=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id,
            "first_name": first_name
        }

        parameters['number'] = number

        if last_name is not None: parameters['last_name'] = last_name
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}

        response = requests.post(f'https://api.telegram.org/bot{self.token}/sendContact', json=parameters)

        if not response.json()['ok']:
            raise Telegram(response.json()['description'])

        return Message(response.json()['result'], self)

    def send_dice(self, chat_id: Union[int, str], emoji: str, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        parameters = {
            "chat_id": chat_id
        }
        
        if reply_to_message_id is not None:
            parameters['reply_to_message_id'] = reply_to_message_id

        if emoji not in ['🎲', '🎯', '🏀', '⚽', '🎳', '🎰']:
            raise TypeError(f'Такой эмодзи {emoji} не допускается.')

        if reply_markup is not None and reply_markup.rows:
            if isinstance(reply_markup, ReplyKeyboardMarkup):
                parameters['reply_markup'] = {'keyboard': reply_markup.rows, 'resize_keyboard': reply_markup.resize_keyboard}
            elif isinstance(reply_markup, InlineKeyboardMarkup):
                parameters['reply_markup'] = {'inline_keyboard': reply_markup.rows}

        response = requests.post(f'https://api.telegram.org/bot{self.token}/sendDice', json=parameters)

        if not response.json()['ok']:
            raise Telegram(response.json()['description'])

        return Message(response.json()['result'], self)

    def send_chat_action(self, chat_id: Union[int, str], action: Union[str, ChatAction]):
        parameters = {
            "chat_id": chat_id,
            "action": action
        }

        response = requests.post(f'https://api.telegram.org/bot{self.token}/sendChatAction', json=parameters)

        if not response.json()['ok']:
            raise Telegram(response.json()['description'])

        return Message(response.json()['result'], self)
    
    def next_step_handler(self, chat_id: int, callback: Callable, *args) -> None:
        self._next_step_handlers.append((str(chat_id), callback, args))

    def polling(self, on_startup: Callable=None, threaded_run: bool=False, thread_max_works: int=10, *args) -> None:
        """
        Запускает процесс опроса событий, выполняя указанную функцию при старте.

        :param on_startup: Функция, которая будет вызвана при запуске опроса (например, для инициализации).
        :param args: Дополнительные аргументы, которые будут переданы в функцию on_startup.
        :param threaded_run: Запуск с потоком.
        :param thread_max_works: Ограничения по потокам(!Чем больше потоков запустится, тем сильнее нагружается процессор!)
        :return: Ничего не возвращает.
        """
        if on_startup is not None:  on_startup(*args)

        if threaded_run:
            executor = ThreadPoolExecutor(thread_max_works)

        while True:
            updates = requests.get(f'https://api.telegram.org/bot{self.token}/getUpdates', params={"offset": self.offset})

            if updates.status_code != 200:
                continue

            updates = updates.json()["result"]

            for update in updates:
                try:
                    self.offset = update["update_id"] + 1

                    if update.get('message', False):
                        
                        for indx, step in enumerate(self._next_step_handlers):
                            if str(update['message']['chat']['id']) == step[0]:
                                if threaded_run:
                                    executor.submit(step[1], Message(update['message'], self), *step[2])
                                else:
                                    step[1](Message(update['message'], self), *step[2])
                                
                                self._next_step_handlers.pop(indx)
                                break
                        
                        for handler_message in self._message_handlers:
                            if handler_message['filters'] is not None and not handler_message['filters'](Message(update['message'], self)):
                                continue

                            if handler_message['commands'] is not None:
                                if isinstance(handler_message['commands'], list):
                                    if not any(update['message']['text'].split()[0] == '/' + command for command in
                                               handler_message['commands']):
                                        continue
                                elif isinstance(handler_message['commands'], str):
                                    if not update['message']['text'].split()[0] == '/' + handler_message['commands']:
                                        continue

                            if isinstance(handler_message['content_types'], str):
                                if not update['message'].get(handler_message['content_types'], False):
                                    continue
                            elif isinstance(handler_message['content_types'], list):
                                if not any(update['message'].get(__type, False) for __type in handler_message['content_types']):
                                    continue

                            if isinstance(handler_message['allowed_chat_type'], str):
                                if update['message']['chat']['type'] != handler_message['allowed_chat_type']:
                                    continue
                            elif isinstance(handler_message['allowed_chat_type'], (tuple, list)):
                                if not any(update['message']['chat']['type'] == _chat_type for _chat_type in handler_message['allowed_chat_type']):
                                    continue

                            message = Message(update['message'], self)
                            try:
                                if threaded_run:
                                    executor.submit(handler_message['func'], message)
                                else:
                                    handler_message['func'](message)
                            except SyntaxError as e:
                                if "'await' outside function" in str(e):
                                    raise SyntaxError('В вашей функции вы вызываете асинхронную функция.Провертье ваш код на наличии EasyGram.Async.types')
                                else:
                                    raise SyntaxError(str(e))
                    elif update.get('callback_query', False):
                        for callback in self._callback_query_handlers:
                            if callback['filters'] is not None and not callback['filters'](Message(update['callback_query'], self)):
                                continue

                            if isinstance(callback['allowed_chat_type'], str):
                                if update['callback_query']['chat']['type'] != callback['allowed_chat_type']:
                                    continue
                            elif isinstance(callback['allowed_chat_type'], (tuple, list)):
                                if not any(update['callback_query']['chat']['type'] == _chat_type for _chat_type in callback['allowed_chat_type']):
                                    continue
                            
                            callback_query = CallbackQuery(update['callback_query'], self)
                            try:
                                if threaded_run:
                                    executor.submit(self._callback_query_handlers['func'], message)
                                else:
                                    self._callback_query_handlers['func'](message)
                            except SyntaxError as e:
                                if "'await' outside function" in str(e):
                                    raise SyntaxError('В вашей функции вы вызываете асинхронную функция.Провертье ваш код на наличии EasyGram.Async.types')
                                else:
                                    raise SyntaxError(str(e))
                except Exception as e:
                    traceback.print_exc()