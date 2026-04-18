from Dekanat import routes

MAIN = [
    ("База знань", "book-marked", routes.BASE),
    ("Контингент", "graduation-cap", routes.CONTINGENT)
]

CONTINGENT = [
    ("Абітурієнти", "file-user", routes.APPLICANTS)
]
