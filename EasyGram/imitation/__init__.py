from flask import Flask, render_template, request, jsonify, make_response
from typing import List, Union, Callable, Tuple
import asyncio
import random
import requests
from ..types import (
Message,
InlineKeyboardMarkup,
ReplyKeyboardMarkup,
ParseMode,
BotCommand,
BotCommandScopeDefault,
BotCommandScopeChat,
BotCommandScopeAllChatAdministrators,
BotCommandScopeChatMember,
BotCommandScopeAllGroupChats,
BotCommandScopeAllPrivateChats,
BotCommandScopeChatAdministrators,
InputFile,
InputPollOption
)
from ..exception import Telegram
from concurrent.futures import ThreadPoolExecutor
import time
import webbrowser
import base64
import traceback

class ExampleBot:
    app = Flask(__name__)

    def __init__(self, token: str, user_id: int=random.randint(1000, 999999), first_name: str='User', last_name: str='Durov', user_name: str='oprosmenya', autoOpen: bool=True):
        self._message_handler = []
        self.client_updates = [] # Обновления для стороны клиента(сайта)
        self.updates = [] # Обновления для стороны бота(серверная часть)
        self.message_id = 1000 # Чтобы в будущем можно было сделать сообщение которое показывает на какое сообщение указывает
        self.commands = []
        self.token = token

        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = user_name
        
        self.autoOpen = autoOpen

        self.app.add_url_rule('/', 'main', self.main)
        self.app.add_url_rule('/getUpdates', 'get_updates', self.get_updates, methods=['GET'])
        self.app.add_url_rule('/sendMessage', 'send_message', self._send_message, methods=['POST'])
        self.app.add_url_rule('/getCommands', 'get_commands', self.get_commands, methods=['GET'])
        self.app.add_url_rule('/getBotData', 'get_botData', self.get_data_bot, methods=['GET'])

    def main(self):
        return render_template('index.html')

    def get_updates(self):
        if self.client_updates:
            msg = jsonify({"updates": self.client_updates})
            self.client_updates = []
            return msg
        else:
            return make_response({"updates": []}, 204)

    def get_data_bot(self):
        response = requests.get(f'https://api.telegram.org/bot{self.token}/getUserProfilePhotos', json={"user_id": self.token.split(':')[0]})
        _response = requests.get(f'https://api.telegram.org/bot{self.token}/getMe')
        __response = requests.get(f'https://api.telegram.org/bot{self.token}/getMyDescription')
        image = None
        desc = None

        if __response.json()['ok']:
            desc = __response.json()['result']['description']

        if not _response.json()['ok']:
            return '', 204

        if response.json()['ok']:
            if response.json()['result']['total_count'] < 1:
                return '', 204
            file_id = response.json()["result"]["photos"][0][-1]["file_id"]

            file_info = requests.get(f'https://api.telegram.org/bot{self.token}/getFile', json={"file_id": file_id})
            if file_info.json()['ok']:
                file_path = file_info.json()["result"]["file_path"]

                image = f'https://api.telegram.org/file/bot{self.token}/{file_path}'
            else: return '', 204

        return {"name": _response.json()['result']['first_name'], "username": _response.json()['result']['username'], "description": desc, "image": image}, 200

    def _send_message(self):
        data = request.json

        self.message_id += 1
        self.updates.append({
            'update_id': random.randint(10000, 9999999),
            'message': {
                'message_id': self.message_id,
                'from': {
                    'id': self.user_id,
                    'is_bot': False,
                    'first_name': self.first_name,
                    'username': self.username,
                    'language_code': 'ru'
                },
                'chat': {
                    'id': self.user_id,
                    'first_name': self.first_name,
                    'username': self.username,
                    'type': 'private'
                },
                'date': 1732283684,
                'text': data['text']
            }
        })
        self._polling()

        return {"ok": True, "message_id": self.message_id-1}, 200

    def get_commands(self):
        print(self.commands)
        if self.commands:
            return self.commands, 200
        else: return '', 204

    def message(self, _filters: Callable=None, content_types: Union[str, List[str]]=None, commands: Union[str, List[str]]=None, allowed_chat_type: Union[str, List[str], Tuple[str]]=None) -> Callable:
        def wrapper(func):
            self._message_handler.append({"_filters": _filters, "func": func, "content_types": content_types, "commands": commands})
        return wrapper

    def send_message(self, chat_id: Union[int, str], text: Union[int, float, str], reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, parse_mode: Union[str, ParseMode]=None, reply_to_message_id: int=None) -> Message:
        self.message_id += 1
        self.client_updates.append({"message": {"message_id": self.message_id+1, "text": str(text),"parse_mode": parse_mode, "reply_to_message_id": reply_to_message_id}})

        return Message({"text": str(text),"parse_mode": parse_mode, "message_id": self.message_id}, self)

    def get_me(self):
        ...

    def set_my_commands(self, commands: List[BotCommand], scope: Union[BotCommandScopeChat, BotCommandScopeDefault, BotCommandScopeChatMember, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats, BotCommandScopeChatAdministrators, BotCommandScopeAllChatAdministrators]=None, language_code: str=None) -> bool:
        self.commands.extend([{"command": command.command, "description": command.description} for command in commands])

    def send_photo(self, chat_id: Union[int, str], photo: Union[InputFile], caption: Union[int, float, str]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, parse_mode: Union[str, ParseMode]=None, reply_to_message_id: int=None):
        _photo = base64.b64encode(photo.file.getvalue()).decode('utf-8')

        self.message_id += 1
        self.client_updates.append({"photo": {"message_id": self.message_id, "photo": _photo, "reply_to_message_id": reply_to_message_id, "caption": caption}})
        
        return Message({"text": str(caption), "parse_mode": parse_mode, "message_id": self.message_id}, self)

    def message_handler(self, _filters: Callable=None, content_types: Union[str, List[str]]=None, commands: Union[str, List[str]]=None, allowed_chat_type: Union[str, List[str], Tuple[str]]=None) -> Callable:
        def wrapper(func):
            self._message_handler.append({"func": func, "filters": _filters, "content_types": content_types, "commands": commands})
        return wrapper

    def callback_query(self) -> Callable:
        ...

    def callback_query_handler(self) -> Callable:
        ...

    def answer_callback_query(self) -> bool:
        ...

    def delete_message(self, chat_id: Union[int, str], message_id: int) -> bool:
        self.client_updates.append({"delete_message": {"message_id": message_id}})

        return True

    def edit_message_text(self, chat_id: Union[int, str], message_id: int, text: Union[int, float, str], parse_mode: Union[str, ParseMode]=None, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None) -> bool:
        self.client_updates.append({"edit_message_text": {"message_id": message_id, "text": text, "parse_mode": parse_mode}})

        return True

    def send_poll(self, chat_id: Union[int, str], question: Union[int, float, str], options: Union[List[InputPollOption], List[str]], question_parse_mode: Union[str, ParseMode]=None, is_anonymous: bool=True, type: str='regular', allows_multiple_answers: bool=False, correct_option_id: int=0, explanation: str=None, explanation_parse_mode: Union[str, ParseMode]=None, open_period: int=None, is_closed: bool=False, reply_markup: Union[ReplyKeyboardMarkup, InlineKeyboardMarkup]=None, reply_to_message_id: int=None) -> Message:
        self.message_id += 1
        parameters = {
            "question": question,
            "options": [],
            "type": type,
            "allows_multiple_answers": allows_multiple_answers,
            "correct_option_id": correct_option_id,
            "explanation": explanation,
            "open_period": open_period,
            "is_closed": is_closed,
            "reply_to_message_id": reply_to_message_id,
            "message_id": self.message_id
        }

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
            for option in options:
                if isinstance(option, InputPollOption):
                    parameters['options'].append({"text": option.text})
                else:
                    parameters['options'].append({"text": option})
        
        self.message_id += 1
        self.client_updates.append({"poll": parameters})

        return Message({"message_id": self.message_id}, self)

    def _polling(self):
        for i in range(len(self.updates)):
            update = self.updates[i]

            if update.get('message', False):
                for message_handler in self._message_handler:
                    if message_handler['_filters'] is not None:
                        if not message_handler['_filters'](Message(update['message'], self)):
                            continue

                    if message_handler['commands'] is not None:
                        if isinstance(message_handler['commands'], list):
                            if not any(update['message']['text'].split()[0] == '/' + command for command in
                                       message_handler['commands']):
                                continue
                        elif isinstance(message_handler['commands'], str):
                            print(update['message']['text'])
                            if not update['message']['text'].split()[0] == '/' + message_handler['commands']:
                                continue

                    if isinstance(message_handler['content_types'], str):
                        if not update['message'].get(message_handler['content_types'], False):
                            continue
                    elif isinstance(message_handler['content_types'], list):
                        if not any(update['message'].get(__type, False) for __type in message_handler['content_types']):
                            continue

                    message = Message(update['message'], self)
                    message_handler['func'](message)

                    self.updates.pop(i)
                    break

    def polling(self):
        webbrowser.open('http://127.0.0.1:5000/')
        self.app.run('0.0.0.0', 5000, False)