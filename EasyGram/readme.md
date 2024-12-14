Установить:
```bash
pip install git+https://github.com/flexyyyapk/EasyGram.git
```

## Быстрый старт

#### Эхо бот(синхронный)
```python
from EasyGram import SyncBot, types

bot = SyncBot('Token here')

@bot.message(content_types='text')
def echo_bot(message: types.Message):
	message.answer(message.text)

bot.polling()
```

#### Эхо бот(асинхронный)
```python
from EasyGram.Async import AsyncBot, types

bot = AsyncBot('Token here')

@bot.message(content_types='text')
async def echo_bot(message: types.Message):
	await message.answer(message.text)

bot.executor()
```

---

#### Бот рандомайзер(синхронный):
```python
from EasyGram import SyncBot, types
from random import randint

bot = SyncBot('Token here')

@bot.message(commands='start')
def start(message: types.Message):
	#Делаем маленькую кнопку
	button = types.ReplyKeyboardMarkup(resize_keyboard=True)
	button.add('От 1 до 10')
	
	message.answer('Привет!', reply_markup=button)

@bot.message(lambda message: message.text == 'От 1 до 10')
def random_number(message: types.Message):
	message.answer(f'Тебе выпало: {randint(1, 10)}!')

bot.polling()
```


#### Бот рандомайзер(асинхронный)
```python
from EasyGram.Async import AsyncBot, types
from random import randint

bot = AsyncBot('Token here')

@bot.message(commands='start')
async def start(message: types.Message):
	#Делаем маленькую кнопку
	button = types.ReplyKeyboardMarkup(resize_keyboard=True)
	button.add('От 1 до 10')
	
	await message.answer('Привет!', reply_markup=button)

@bot.message(lambda message: message.text == 'От 1 до 10')
async def random_number(message: types.Message):
	await message.answer(f'Тебе выпало: {randint(1, 10)}!')

bot.executor()
```
