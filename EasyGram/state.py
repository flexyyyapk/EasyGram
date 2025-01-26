from typing import Union

class State:
    """
    Класс для хранения состояний пользователей.
    """

    var_name = None

    def __init__(self):
        self.state_registry = {}

    def set_state(self, chat_id: int, user_id: int, value: any=None) -> None:
        if chat_id in self.state_registry:
            self.state_registry[chat_id][user_id] = value if value is not None else True
        else:
            self.state_registry[chat_id] = {user_id: value if value is not None else True}
    
    def get_state(self, chat_id: int, user_id: int) -> Union[any, bool]:
        if chat_id in self.state_registry:
            if user_id in self.state_registry[chat_id]:
                return self.state_registry[chat_id][user_id]
        return False

    def remove_state(self, chat_id: int, user_id: int) -> None:
        if chat_id in self.state_registry:
            if user_id in self.state_registry[chat_id]:
                del self.state_registry[chat_id][user_id]

class StatesGroupMeta(type):

    class_name = None

    def __new__(cls, name, bases, attrs):
        for key, value in attrs.items():
            if isinstance(value, State):
                value.var_name = key
            if str(key) == '__qualname__':
                cls.class_name = value
        return super().__new__(cls, name, bases, attrs)

class StatesGroup(metaclass=StatesGroupMeta):
    """
    Класс для хранения состояний пользователей.
    """
    variables = {}

    def __init_subclass__(cls):
        super().__init_subclass__()

        for key, value in cls.__dict__.items():
            if isinstance(value, State):
                value.class_name = cls.__name__
                cls.variables[key] = value

class StateException(Exception):
    pass

class StateRegExp:
    """
    Класс для регулярного выражения состояния или просто проверка состояния что он вообще есть у пользователя.
    Пример:
        Проверка состояния на регулярное выражение:
            StateRegExp('имя состояния', 'регулярное выражение')
        Проверка состояние с классом и с регулярным выражением:
            class Test(StatesGroup):
                name = State()
            StateRegExp(Test.name, 'регулярное выражение')
        Проверка состояния без регулярного выражения:
            StateRegExp(Класс.имя_поля или 'имя состояния')
    """
    def __init__(self, state_name: Union[str, State], reg_exp: str=None):
        if isinstance(state_name, State):
            self.state_name = state_name.var_name
        else:
            self.state_name = state_name
        self.reg_exp = reg_exp

        if self.state_name not in StatesGroup.variables:
            raise StateException(f'State {self.state_name} не найден.')

    def __str__(self):
        return f'{self.state_name}:{self.reg_exp}'