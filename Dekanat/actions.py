from enum import StrEnum


class Actions(StrEnum):
    def __new__(cls, code: str, title: str, description: str):
        obj = str.__new__(cls, code)
        obj._value_ = code
        obj.title_attr = title
        obj.description_attr = description
        return obj