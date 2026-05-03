from Dekanat import routes

MAIN = [
    ("База знань", "book-marked", routes.IDENTITY_DOCUMENT_TYPE_LIST),
    ("Контингент", "graduation-cap", routes.CONTINGENT)
]

CONTINGENT = [
    ("Абітурієнти", "file-user", routes.APPLICANTS)
]

BASE = [
    ("Типи посвідчень особи", "file-user", routes.IDENTITY_DOCUMENT_TYPE_LIST)
]
