from .utils import CheckDict
from typing import Optional, Union
import requests
from .exception import ButtonParameterErorr

class GetMe:
    def __init__(self, bot):
        self.id: int = requests.get(f'https://api.telegram.org/bot{bot.token}/getMe').json()['result']['id']
        self.other = requests.get(f'https://api.telegram.org/bot{bot.token}/getMe').json()['result']

class KeyboardButton:
    """
    Keyboard object.
    :param text: name
    :return: self
    """
    def __init__(self, text: Union[int, float, str]):
        self.keyboard = {'text': text}

class ReplyKeyboardMarkup:
    """
    ReplyKeyboardMarkup object.
    :param width: row length
    :param resize_keyboard: resize keyboard
    """
    def __init__(self, row_width: int=3, resize_keyboard: bool=False):
        self.rows = []
        self.row_width = row_width
        self.resize_keyboard = resize_keyboard

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

class InlineKeyboardButton:
    def __init__(self, text: Union[int, float, str], url: str=None, callback_data: str=None):
        self.keyboard = {'text': text}

        if url is None and callback_data is None:
            raise ButtonParameterErorr('Для создания кнопки необходимо указать либо "url", либо "callback_data".')

        if url is not None and callback_data is not None:
            raise ButtonParameterErorr('Для создания кнопки необходимо указать либо "url", либо "callback_data"')

        if url is not None:
            self.keyboard.update({'url': url})
        elif callback_data is not None:
            self.keyboard.update({'callback_data': callback_data})

class InlineKeyboardMarkup:
    def __init__(self, row_width: int=3):
        self.rows = []
        self.row_width = row_width

    def add(self, *args: InlineKeyboardButton) -> None:
        """
        Добавления Inline Кнопки.
        :param args: InlineKeyboardButton object
        :return: None
        """
        _butt = []

        for butt in args:
            if isinstance(butt, InlineKeyboardButton):
                _butt.append({'text': butt.keyboard['text']})

            if len(_butt) == self.row_width:
                self.rows.append(_butt)
                _butt = []
        else:
            if _butt:
                self.rows.append(_butt)

class Message:
    """
    Message object.
    """
    def __init__(self, message: dict, bot):
        self.message_id: Optional[int] = message.get('message_id', None)
        self.from_user: Optional[User] = User(message['from']) if CheckDict(message, 'from') else None
        self.chat: Optional[Chat] = Chat(message['chat']) if CheckDict(message, 'chat') else None
        self.date: Optional[int] = message.get('date', None)
        self.text: Optional[str] = message.get('text', None)

        self.bot = bot

    def answer(self, text: str, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, parse_mode: str=None) -> None:
        self.bot.send_message(self.chat.id, text, reply_markup, parse_mode)

class CallbackQuery:
    def __init__(self, callback_query: dict, bot):
        self.id: Optional[int] = callback_query.get('id', None)
        try:
            callback_query['message']['from']['id'] = callback_query['from']['id']
        except:
            pass
        self.message: Optional[Message] = Message(callback_query.get('message', None), bot)
        self.from_user: Optional[User] = User(callback_query['from']) if CheckDict(callback_query, 'from') else None
        self.chat: Optional[Chat] = Chat(callback_query['message']['chat']) if CheckDict(callback_query['message'], 'chat') else None
        self.data: str = callback_query['data']

        self.bot = bot

    def answer(self, text: Union[str, int, float], show_alert: bool=False):
        self.bot.answer_callback_query(self.id, str(text), show_alert)

class User:
    """
    User object.
    """
    def __init__(self, user: dict):
        self.id: Optional[int] = user.get('id', None)
        self.is_bot: Optional[bool] = user.get('is_bot', None)
        self.first_name: Optional[str] = user.get('first_name', None)
        self.username: Optional[str] = user.get('username', None)
        self.last_name: Optional[str] = user.get('last_name', None)

class Chat:
    """
    Chat object.
    """
    def __init__(self, chat: dict):
        self.id: Optional[int] = chat.get('id', None)
        self.first_name: Optional[str] = chat.get('first_name', None)
        self.title: Optional[str] = self.first_name
        self.username: Optional[str] = chat.get('username', None)
        self.type: Optional[str] = chat.get('type', None)

class ChatType:
    def __init__(self):
        self.private = 'private'
        self.group = 'group'
        self.supergroup = 'supergroup'
        self.channel = 'channel'

class ParseMode:
    def __init__(self):
        self.html = 'html'
        self.markdown = 'markdown'
        self.markdownv2 = 'markdownv2'
        self.HTML = html
        self.MARKDOWN = markdown
        self.MARKDOWNV2 = markdownv2
        self.MarkDown = markdown
        self.MarkDownV2 = markdownv2

class ContentType:
    def __init__(self):
        self.text = 'text'
        self.photo = 'photo'
        self.video = 'video'
        self.audio = 'audio'
        self.document = 'document'
        self.animation = 'animation'
        self.voice = 'voice'
        self.video_note = 'video_note'
        self.location = 'location'
        self.contact = 'contact'
        self.sticker = 'sticker'
        self.poll = 'poll'
        self.dice = 'dice'
        self.game = 'game'
        self.invoice = 'invoice'
        self.venue = 'venue'
