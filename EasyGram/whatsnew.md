## Что нового?
С новой версии `0.0.2` добавилось:
- В `SyncBot` и `AsyncBot` добавлена возможность запускать ботов с многопоточностью, дабы придать больше скорости вашему боту!

Чтобы сделать это в `SyncBot` требуется указать параметр `threaded_run=True`.
### Пример:
```python
from EasyGram import SyncBot

bot = SyncBot('Token')

#... Остальной код

bot.polling(threaded_run=True)
```

С `AsyncBot` тоже нужно указать параметр `threaded_run=True` в `executor()` или `polling()`.
### Пример:
```python
from EasyGram.Async import AsyncBot

bot = AsyncBot('Token')

#... Остальной код

bot.executor(threaded_run=True)
```
*По желанию можно установить параметр thread_max_works=15.Это максимальное кол-во потоков которое можно использовать.!Главное не ставить много, иначе будет сильная нагрузка на процессор!*
- Теперь можно добавить команды в панель команд(лист с командами, менюшка команд, как угодно) с помощью `set_my_commands()`

### Пример:
```python
from EasyGram.Async import AsyncBot, types

bot = AsyncBot('Token')

commands = [
    types.BotCommand(command='start', description='Run bot'),
    types.BotCommand(command='help', description='help')
]

bot.set_my_commands(commands, scope=types.BotCommandScopeAllGroupChats()) #scope по желанию
```

Тоже самое и с `SyncBot`
### Пример:
```python
from EasyGram import SyncBot, types

bot = SyncBot('Token')

commands = [
    types.BotCommand(command='start', description='Run bot')
]

bot.set_my_commands(commands, scope=types.BotCommandScopeAllGroupChats()) #scope по желанию
```
- Появились два метода в объекте `InlineKeyboardMarkup`: `add_tostorage()` и `add_keyboards()`. 

Первый `add_tostorage(*args: types.InlineKeyboardButton)` добавляет объекты в список `types.InlineKeyboardMarkup.storage`, а второй `types.InlineKeyboardMarkup.add_keyboards()` в один ряд добавляет кнопки.

- Добавлен метод удаления сообщения.
### Пример:
С `SyncBot`
```python
from EasyGram import SyncBot, types

bot = SyncBot('Token here')

#... остальной код

@bot.message()
def messages(message: types.Message):
    bot.delete_message(message.chat.id, message.message_id-1) #Удаления предыдущего сообщения
    message.delete() #Удаления этого сообщения, т.е от пользователя

#Удаления в CallbackQuery
@bot.callback_query()
def call(call: types.CallbackQuery):
    bot.delete_message(call.chat.id, call.message.message_id-1)
    call.message.delete() # Удаления сообщения куда пользовать нажал на кнопку
    
bot.polling()
```
---
С `AsyncBot`
```python
from EasyGram.Async import AsyncBot, types

bot = AsyncBot('Token here')

#... остальной код

@bot.message()
async def messages(message: types.Message):
    await bot.delete_message(message.chat.id, message.message_id-1) #Удаления предыдущего сообщения
    await message.delete() #Удаления этого сообщения, т.е от пользователя

#Удаления в CallbackQuery
@bot.callback_query()
async def call(call: types.CallbackQuery):
    await bot.delete_message(call.chat.id, call.message.message_id-1)
    await call.message.delete() # Удаления сообщения куда пользовать нажал на кнопку

bot.executor()
```

- Добавлен метод редактирования сообщения.

### Пример:
С `SyncBot`
```python
from EasyGram import SyncBot, types
from time import sleep

bot = SyncBot('Token here')

#... остальной код

@bot.message()
def message(message: types.Message):
    msg: types.Message = message.answer('Привет')
    sleep(10)# !!!!!Работает корректно только если в bot.polling() установлен параметр threaded_run=True
    msg.edit('Как дела?')

bot.polling(threaded_run=True)
```
С `AsyncBot`
```python
from EasyGram.Async import AsyncBot, types
from asyncio import sleep

bot = AsyncBot('Token here')

#... остальной код

@bot.message()
async def message(message: types.Message):
    msg: types.Message = await message.answer('Привет')
    await sleep(10)
    await msg.edit('Как дела?')

bot.executor()
```

- Добавлен метод отправления опроса.
### Пример:
С `SyncBot`
```python
from EasyGram import SyncBot, types
from time import sleep

bot = SyncBot('Token here')

#... остальной код

@bot.message()
def message(message: types.Message):
    message.send_poll('Как дела?', [types.InputPollOption('<b>Отлично</b>', text_parse_mode='html'), types.InputPollOption('Плохо')])
    bot.send_poll(message.from_user.id, 'Как дела?', [types.InputPollOption('<b>Отлично</b>', text_parse_mode='html'), types.InputPollOption('Плохо')])

bot.polling()
```
С `AsyncBot`
```python
from EasyGram.Async import AsyncBot, types
from asyncio import sleep

bot = AsyncBot('Token here')

#... остальной код

@bot.message()
async def message(message: types.Message):
    await message.send_poll('Как дела?', [types.InputPollOption('<b>Отлично</b>', text_parse_mode='html'), types.InputPollOption('Плохо')])
    await bot.send_poll(message.from_user.id, 'Как дела?', [types.InputPollOption('<b>Отлично</b>', text_parse_mode='html'), types.InputPollOption('Плохо')])

bot.executor()
```

В объекте `ParseMode` добавлены методы для форматирования текста
```python
from EasyGram.types import ParseMode

print(ParseMode.hbold('test')) # <b>test</b>
print(ParseMode.hitalic('test')) # <i>test</i>
print(ParseMode.hstrikeline('test')) # <s>test</s>
print(ParseMode.hunderline('test')) # <u>test</u>
print(ParseMode.hblockquote('test')) # <blockquote>test</blockquote>
print(ParseMode.hcode('test')) # <code>test</code>
print(ParseMode.hprecode(lang='python', text='test')) # <pre><code class="python">test</code></pre>
```

- Добавлен метод `next_step_handler()`.С помощью него можно вызвать функцию как только пользователь отправит сообщение.
### Пример:
С `SyncBot`
```python
from EasyGram import SyncBot, types

bot = SyncBot('Token here')

@bot.message(commands='start')
def start(message: types.Message):
    message.reply('Привет, введи своё имя.')
    bot.next_step_handler(message.chat.id, nexts) #Ожидания сообщения от пользователя
def nexts(message: types.Message):
    message.answer(f'Приятно познакомиться {message.text}')

bot.polling()
```
С 'AsyncBot'
```python
from EasyGram.Async import AsyncBot, types

bot = AsyncBot('Token here')

@bot.message(commands='start')
async def start(message: types.Message):
    await message.answer('Привет, введи своё имя.')
    await bot.next_step_handler(message.chat.id, nexts) #Ожидания сообщения от пользователя
async def nexts(message: types.Message):
    await message.answer(f'Приятно познакомиться {message.text}')

bot.executor()
```

- Добавлены новые методы в `SyncBot`/`AsyncBot`:
1. `delete_message()`
2. `edit_message_text()`
3. `send_poll()`
4. `send_audio()`
5. `send_documen()`
6. `send_animation()`
7. `send_voice()`
8. `send_video()`
9. `send_video_note()`
10. `send_paid_media()`
11. `send_contact()`
12. `send_dice()`
13. `send_chat_action()`

- Добавлены дополнительные методы к классу Message:
1. `types.Message.delete()`
2. `types.Message.edit()`
3. `types.Message.reply()`
4. `types.Message.send_poll()`
5. `types.Message.send_audio()`
6. `types.Message.send_document()`
7. `types.Message.send_animation()`
8. `types.Message.send_voice()`
9. `types.Message.send_video()`
10. `types.Message.send_video_note()`
11. `types.Message.send_paid_media()`
12. `types.Message.send_contact()`
13. `types.Message.send_dice()`
14. `types.Message.send_chat_action()`

## Что добавить ещё?
Связаться:
- 📞💌Telegram channel: [Channel](https://t.me/oprosmenya)