## Что нового?

С новой версии `0.0.3` добавилось:

- Добавился метод в классе `SyncBot`: `start_polling()`
- Добавлен класс `Poll` в types `ах
- Переименован класс `InputPollOption` на `PollOption` для удобства и схожести с именами как в Telegram API
- Добавлен обработчик `poll`:

### Пример:

```python
from EasyGram import SyncBot, types

bot = ...

# Все опросы
@bot.poll()
def all_polls(poll: types.Poll):
    print(poll) # Вывод словаря в строки

bot.start_polling()
```

- Исправлены ошибки в `EasyGram.Async`
- Добавлены методы edit в объектах `Message`
- Добавлен класс `StateRegExp` в `EasyGram.state`:

### Пример:

```python
from EasyGram import SyncBot, types
from EasyGram.state import State, StatesGroup, StateRegExp

bot = ...

class States(StatesGroup):
    room = State()

@bot.message(commands='start')
def start(message: types.Message):
    message.answer('Привет, введи своё имя.')
    States.room.set_state(message.chat.id, message.from_user.id, 'Enter name')

@bot.message(state=StateRegExp(States.room, 'Enter name'))
def entered_name(message: types.Message, data: str):
    message.reply(f'Твоё имя: {message.text}')
    States.room.remove_state(message.chat.id, message.from_user.id)

bot.polling()
```

- Добавлен метод `query_next_step_handler`, схож с `next_step_handler`

## Что добавить ещё?

Связаться:

- 📞💌Telegram channel: [Channel](https://t.me/oprosmenya)
