from enum import StrEnum


class Actions(StrEnum):
    IDENTITY_DOCUMENT_TYPE_LIST = ("identity_document_type:list", "Перегляд списку типів паспортів", "Дозволяє перегляд списку типів паспортів")
    IDENTITY_DOCUMENT_TYPE_ADD = ("identity_document_type:add", "Додавання типів паспортів", "Дозволяє додавання нових типів паспортів")
    IDENTITY_DOCUMENT_TYPE_EDIT = ("identity_document_type:edit", "Редагування типів паспортів", "Дозволяє редагування існуючих типів паспортів")
    IDENTITY_DOCUMENT_TYPE_DELETE = ("identity_document_type:delete", "Видалення типів паспортів", "Дозволяє видалення існуючих типів паспортів")
    IDENTITY_DOCUMENT_TYPE_VIEW = ("identity_document_type:view", "Перегляд деталізованої інформації про тип паспорту", "Дозволяє переглядати деталізовану інформацію про тип паспорту")

    def __new__(cls, code: str, title: str, description: str):
        obj = str.__new__(cls, code)
        obj._value_ = code
        obj.title_attr = title
        obj.description_attr = description
        return obj
