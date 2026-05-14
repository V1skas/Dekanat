from enum import StrEnum


class Actions(StrEnum):
    IDENTITY_DOCUMENT_TYPE_LIST = ("identity_document_type:list", "Перегляд списку типів паспортів", "Дозволяє перегляд списку типів паспортів")
    IDENTITY_DOCUMENT_TYPE_ADD = ("identity_document_type:add", "Додавання типів паспортів", "Дозволяє додавання нових типів паспортів")
    IDENTITY_DOCUMENT_TYPE_EDIT = ("identity_document_type:edit", "Редагування типів паспортів", "Дозволяє редагування існуючих типів паспортів")
    IDENTITY_DOCUMENT_TYPE_DELETE = ("identity_document_type:delete", "Видалення типів паспортів", "Дозволяє видалення існуючих типів паспортів")
    IDENTITY_DOCUMENT_TYPE_VIEW = ("identity_document_type:view", "Перегляд деталізованої інформації про тип паспорту", "Дозволяє переглядати деталізовану інформацію про тип паспорту")

    KINSHIP_LIST = ("kinship:list", "Перегляд списку типів родичів", "Дозволяє переглядати список типів родичів")
    KINSHIP_ADD = ("kinship:add", "Додавання типів родичів", "Дозволяє додавати нові типи родичів")
    KINSHIP_EDIT = ("kinship:edit", "Редагування типів родичів", "Дозволяє редагувати типи родичів")
    KINSHIP_DELETE = ("kinship:delete", "Видалення типів родичів", "Дозволяє видаляти типи родичів")
    KINSHIP_VIEW = ("kinship:view", "Перегляд деталізованої інформації про тип родича", "Дозволяє перегляд деталізованої інформації про тип родича")

    SPECIAL_CONDITION_LIST = ("special_condition:list", "Перегляд списку спеціальних умов", "Дозволяє переглядати список спеціальних умов вступу")
    SPECIAL_CONDITION_ADD = ("special_condition:add", "Додавання спеціальних умов", "Дозволяє додавати нові спеціальні умови вступу")
    SPECIAL_CONDITION_EDIT = ("special_condition:edit", "Редагування спеціальних умов", "Дозволяє редагувати спеціальні умови вступу")
    SPECIAL_CONDITION_DELETE = ("special_condition:delete", "Видалення спеціальних умов", "Дозволяє видаляти спеціальні умови вступу")
    SPECIAL_CONDITION_VIEW = ("special_condition:view", "Перегляд деталізованої інформації про спеціальну умову", "Дозволяє перегляд деталізованої інформації про спеціальну умову вступу")

    ROLE_LIST = ("role:list", "Перегляд списку ролей", "Дозволяє перегляд списку ролей")
    ROLE_ADD = ("role:add", "Додавання ролей", "Дозволяє додавати нові ролі")
    ROLE_EDIT = ("role:edit", "Редагування ролей", "Дозволяє редагувати існуючі ролі")
    ROLE_DELETE = ("role:delete", "Видалення ролей", "Дозволяє видаляти існуючі ролі")
    ROLE_VIEW = ("role:view", "Детальний перегляд ролей", "Дозволяє перегляд детальної інформації про ролі")

    WORKER_LIST = ("worker:list", "Перегляд списку користувачів", "Дозволяє перегляд списку користувачів")
    WORKER_ADD = ("worker:add", "Додавання користувачів", "Дозволяє додавати нових користувачів")
    WORKER_EDIT = ("worker:edit", "Редагування користувачів", "Дозволяє редагування існуючих користувачів")
    WORKER_DELETE = ("worker:delete", "Видалення користувачів", "Дозволяє видалення існуючих користувачів")
    WORKER_VIEW = ("worker:view", "Детальний перегляд користувачів", "Дозволяє переглядати деталізованої інформації про користувачів")

    def __new__(cls, code: str, title: str, description: str):
        obj = str.__new__(cls, code)
        obj._value_ = code
        obj.title_attr = title
        obj.description_attr = description
        return obj
