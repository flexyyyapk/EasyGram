import requests
import asyncio

from typing_extensions import override
from typing import Union, List, BinaryIO, Callable
from io import BytesIO, IOBase
from pathlib import Path

from ..types import (
    Message as BaseMessage,
    User as BaseUser,
    Chat as BaseChat,
    ReplyKeyboardMarkup as BaseRKM,
    KeyboardButton as BaseKB,
    InlineKeyboardMarkup as BaseIKM,
    InlineKeyboardButton as BaseIKB,
    CallbackQuery as BaseCQ,
    ChatType as BaseChT,
    ParseMode as BasePM,
    ContentType as BaseCnT,
    Poll as BasePoll
)

from ..exception import ButtonParameterErorr, Telegram

class GetMe:
    """
    Получения информации о боте
    """
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
    :param row_width: row length
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

        for butt in args:
            if isinstance(butt, KeyboardButton):
                _butt.append({'text': butt.keyboard['text']})
            else:
                _butt.append({'text': butt})

            if len(_butt) == self.row_width:
                self.rows.append(_butt)
                _butt = []
        else:
            if _butt:
                self.rows.append(_butt)

class InlineKeyboardButton(BaseIKB):
    """
    InlineKeyboardButton object применяется в EasyGram.Async.types.InlineKeyboardMarkup
    """
    def __init__(self, text: str, url: str=None, callback_data: str=None, onClick: Callable=None):
        super().__init__(text, url, callback_data)

class InlineKeyboardMarkup(BaseIKM):
    """
    InlineKeyboardMarkup object применяется для создании кнопки.
    """
    def __init__(self, row_width: int=3):
        super().__init__(row_width)

    @override
    def add(self, *args: InlineKeyboardButton) -> None:
        """
        Добавления Inline Кнопки.
        :param args: InlineKeyboardButton object
        :return: None
        """
        _butt = []

        for butt in args:
            if isinstance(butt, InlineKeyboardButton):
                _butt.append(butt.keyboard)
            elif isinstance(butt, BaseIKM):
                raise ValueError('Тип кнопки из EasyGram.types.InlineKeyboardButton не принимается')
            else:
                raise ValueError('Неизвестный тип')

            if len(_butt) == self.row_width:
                self.rows.append(_butt)
                _butt = []
        else:
            if _butt:
                self.rows.append(_butt)
    @override
    def add_tostorage(self, *args: InlineKeyboardButton) -> None:
        """
        Добавляет кнопки в список, чтобы можно было массово добавить в один ряд
        :param args: InlineKeyboardButton object.
        :return: None
        """
        if not args: return None
        self.storage.extend(args)
    @override
    def add_keyboards(self) -> None:
        """
        Добавляет массово в один ряд
        :return: None
        """
        self.add(*self.storage)
        self.storage = []

class ParseMode(BasePM):
    """
    Форматирования текста.
    """
    def __init__(self):
        super().__init__()

class PollOption:
    """
    Класс для создания варианта ответа в опросе
    """
    def __init__(self, text: Union[int, float, str], text_parse_mode: Union[str, ParseMode]=None):
        if len(text) > 1_000:
            try:
                raise Telegram('Слишком длинный текст.')
            except Telegram as e:
                traceback.print_exc(e)
                return

        self.text = text
        self.text_parse_mode = text_parse_mode

class InputFile:
    """
    Класс для безопасного вставки файла.Рекомендуется для использования
    """
    def __init__(self, file: Union[IOBase, BinaryIO, BytesIO, Path]):
        if isinstance(file, (IOBase, BinaryIO, BytesIO)):
            self.file = file
        elif isinstance(file, Path):
            with open(file, 'rb') as f:
                self.file = BytesIO(f.read())
        else:
            raise TypeError('Unknow file type')

class ChatAction:
    """
    Класс для определения действий в чате.
    """
    TYPING = 'typing'
    UPLOAD_PHOTO = 'upload_photo'
    RECORD_VIDEO = 'record_video'
    UPLOAD_VIDEO = 'upload_video'
    RECORD_VOICE = 'record_voice'
    UPLOAD_VOICE = 'upload_voice'
    UPLOAD_DOCUMENT = 'upload_document'
    CHOOSE_STIKER = 'choose_sticker'
    FIND_LOCATION = 'find_location'
    RECORD_VIDEO_NOTE = 'record_video_note'
    UPLOAD_VIDEO_NOTE = 'upload_video_note'
    typing = 'typing'
    upload_photo = 'upload_photo'
    record_video = 'record_video'
    upload_video = 'upload_video'
    record_voice = 'record_voice'
    upload_voice = 'upload_voice'
    upload_document = 'upload_document'
    choose_sticker = 'choose_sticker'
    find_location = 'find_location'
    record_video_note = 'record_video_note'
    upload_video_note = 'upload_video_note'

class Poll(BasePoll):
    """
    Класс для создания опроса.
    """
    def __init__(self, poll: dict):
        super().__init__(poll)

class Message(BaseMessage):
    """
    Async Message object.
    """

    def __init__(self, message, bot):
        super().__init__(message, bot)

    @override
    async def answer(self, text: str, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, parse_mode: str=None) -> 'Message':
        """
        Отправляет ответное сообщение.
        """
        return await self.bot.send_message(self.chat.id, text, reply_markup, parse_mode)
    
    @override
    async def edit(self, text: str, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, parse_mode: str=None) -> bool:
        """
        Редактирует сообщение.
        """
        return await self.bot.edit_message_text(self.chat.id, self.message_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
    
    @override
    async def delete(self):
        """
        Удаляет сообщение.
        """
        await self.bot.delete_message(self.chat.id, self.message_id)
    
    @override
    async def send_poll(self, question: Union[int, float, str], options: Union[List[PollOption], List[str]], question_parse_mode: Union[str, ParseMode]=None, is_anonymous: bool=True, type: str='regular', allows_multiple_answers: bool=False, correct_option_id: int=0, explanation: str=None, explanation_parse_mode: Union[str, ParseMode]=None, open_period: int=None, is_closed: bool=False, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None) -> 'Message':
        """
        Отправляет опрос.
        """
        return await self.bot.send_poll(self.chat.id, question, options, question_parse_mode, is_anonymous, type, allows_multiple_answers, correct_option_id, explanation, explanation_parse_mode, open_period, is_closed, reply_markup)

    @override
    async def send_audio(self, audio: InputFile, caption: str=None, parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None) -> 'Message':
        """
        Отправляет аудиофайл.
        """
        return await self.bot.send_audio(self.chat.id, audio, caption, parse_mode, reply_markup)
    
    @override
    async def send_document(self, document: InputFile, caption: str = None, parse_mode: Union[str, ParseMode] = None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup] = None) -> 'Message':
        """
        Отправляет документ.
        """
        return await self.bot.send_document(self.chat.id, document, caption, parse_mode, reply_markup)
    
    @override
    async def send_animation(self, animation: InputFile, caption: str = None, parse_mode: Union[str, ParseMode] = None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup] = None) -> 'Message':
        """
        Отправляет анимацию.
        """
        return await self.bot.send_animation(self.chat.id, animation, caption, parse_mode, reply_markup)
    
    @override
    async def send_voice(self, voice: InputFile, caption: str = None, parse_mode: Union[str, ParseMode] = None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup] = None) -> 'Message':
        """
        Отправляет голосовое сообщение.
        """
        return await self.bot.send_voice(self.chat.id, voice, caption, parse_mode, reply_markup)
    
    @override
    async def send_video(self, video: InputFile, caption: str = None, parse_mode: Union[str, ParseMode] = None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup] = None) -> 'Message':
        """
        Отправляет видео.
        """
        return await self.bot.send_video(self.chat.id, video, caption, parse_mode, reply_markup)
    
    @override
    async def send_video_note(self, video_note: InputFile, caption: str = None, parse_mode: Union[str, ParseMode] = None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup] = None) -> 'Message':
        """
        Отправляет видеозаметку.
        """
        return await self.bot.send_video_note(self.chat.id, video_note, caption, parse_mode, reply_markup)
    
    @override
    async def send_paid_media(self, paid_media: InputFile, caption: str = None, parse_mode: Union[str, ParseMode] = None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup] = None) -> 'Message':
        """
        Отправляет платный контент.
        """
        return await self.bot.send_paid_media(self.chat.id, paid_media, caption, parse_mode, reply_markup)
    
    @override
    async def send_contact(self, number: str, first_name: str, last_name: str = None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup] = None) -> 'Message':
        """
        Отправляет контакт.
        """
        return await self.bot.send_contact(self.chat.id, number, first_name, last_name, reply_markup)
    
    @override
    async def send_dice(self, emoji: str, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup] = None) -> 'Message':
        return await self.bot.send_dice(self.chat.id, emoji, reply_markup)
    
    @override
    async def send_chat_action(self, action: Union[ChatAction, str]):
        """
        Отправляет действие в чате.
        """
        await self.bot.send_chat_action(self.chat.id, action)
    
    @override
    async def reply(self, text: str, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, parse_mode: str=None) -> 'Message':
        """
        Отвечает на сообщение.
        """
        return await self.bot.send_message(self.chat.id, text, reply_markup, parse_mode, reply_to_message_id=self.message_id)

class CallbackQuery(BaseCQ):
    """
    Класс для обработки callback-запросов.
    """
    def __init__(self, callback_query: dict, bot):
        super().__init__(callback_query, bot)
        self.message = Message(callback_query['message'], bot)

    @override
    async def answer(self, text: Union[str, int, float], show_alert: bool=False):
        """
        Отвечает на callback-запрос.
        """
        await self.bot.answer_callback_query(self.id, text, show_alert)

class User(BaseUser):
    def __init__(self, user: dict):
        super().__init__(user)

class Chat(BaseChat):
    def __init__(self, chat: dict):
        super().__init__(chat)

class ChatType(BaseChT):
    """
    Класс для определения типа чата.
    """
    def __init__(self):
        super().__init__()

class ContentType(BaseCnT):
    """
    Класс для определения типа контента.
    """
    def __init__(self):
        super().__init__()

class BotCommand:
    """
    Класс для создания команды бота.
    """
    def __init__(self, command: str, description: str):
        self.command = command
        self.description = description

class BotCommandScopeDefault:
    """
    Класс для определения области действия команды бота.
    """
    def __init__(self):
        self.type = 'default'

class BotCommandScopeAllPrivateChats:
    """
    Класс для определения области действия команды бота.
    """
    def __init__(self):
        self.type = 'all_private_chats'

class BotCommandScopeAllGroupChats:
    """
    Класс для определения области действия команды бота.
    """
    def __init__(self):
        self.type = 'all_group_chats'

class BotCommandScopeAllChatAdministrators:
    """
    Класс для определения области действия команды бота.
    """
    def __init__(self):
        self.type = 'all_chat_administrators'

class BotCommandScopeChat:
    """
    Класс для определения области действия команды бота.
    """
    def __init__(self, chat_id: Union[int, str]):
        self.type = 'chat'
        self.chat_id = chat_id

class BotCommandScopeChatAdministrators:
    """
    Класс для определения области действия команды бота.
    """
    def __init__(self, chat_id: Union[int, str]):
        self.type = 'chat_administrators'
        self.chat_id = chat_id

class BotCommandScopeChatMember:
    """
    Класс для определения области действия команды бота.
    """
    def __init__(self, chat_id: Union[int, str], user_id: int):
        self.type = 'chat_member'
        self.chat_id = chat_id
        self.user_id = user_id