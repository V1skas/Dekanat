FROM python:3.13-slim

WORKDIR /Dekanat

# Reflex требует unzip и curl для скачивания внутреннего JS-движка (bun)
RUN apt-get update && apt-get install -y unzip curl && rm -rf /var/lib/apt/lists/*

# Копируем конфигурацию uv
COPY pyproject.toml uv.lock* ./

# Моментально устанавливаем зависимости
RUN pip install uv
RUN uv sync

# Копируем весь оставшийся код проекта
COPY alembic.ini rxconfig.py update.py deploy.py entrypoint.sh ./
COPY Dekanat/ ./Dekanat/
COPY alembic ./alembic/
COPY assets/ ./assets/

# Настройки для продакшена
ENV DB_URL="sqlite:///data/reflex.db"

ENTRYPOINT [ "sh", "entrypoint.sh" ]

# Запускаем Reflex. В режиме prod он сам будет раздавать и статику, и логику.
CMD ["uv", "run", "reflex", "run", "--env", "prod"]
