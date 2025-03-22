from typing import Union, Any, Optional

class State:
    """
    Класс для хранения состояний пользователей.
    """

    var_name = None

    def __init__(self):
        ...

    def __str__(self) -> str:
        return str(self.var_name)

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
    user_registers = {}

    def __init_subclass__(cls):
        super().__init_subclass__()

        for key, value in cls.__dict__.items():
            if isinstance(value, State):
                value.class_name = cls.__name__
                cls.variables[key] = value
    
    @classmethod
    def set_state(cls, state: State, user_id: int, **kwargs) -> None:
        cls.user_registers.update({int(user_id): {"state": state, "kwargs": kwargs}})
    
    @classmethod
    def get_state(cls, user_id: int) -> str:
        values = cls.user_registers.get(int(user_id), None)
        return None if values is None else f'{values["state"]}'
    
    @classmethod
    def get_value(cls, user_id: int) -> Optional[dict]:
        values = cls.user_registers.get(int(user_id), None)
        return None if values is None else values["kwargs"]

    @classmethod
    def remove_state(cls, user_id: int) -> None:
        cls.user_registers.pop(int(user_id), None)

class StateException(Exception):
    pass

class FSMContext:
    def __init__(self, user_id: int):
        self.user_id = int(user_id)
    
    def set_state(self, state: State, **kwargs) -> None:
        StatesGroup.set_state(state, self.user_id, **kwargs)
    
    def get_state(self) -> str:
        return StatesGroup.get_state(self.user_id)
    
    def get_value(self) -> Optional[dict]:
        return StatesGroup.get_value(self.user_id)
    
    def finish(self) -> None:
        StatesGroup.remove_state(self.user_id)
    
    def __str__(self) -> str:
        return str(self.user_id)