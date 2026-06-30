#!/bin/sh
set -e

# ============================================================================
# Сборка статического фронта Reflex ЛОКАЛЬНО (на машине с поддержкой AVX —
# именно тут запускается bun). Результат складывается в ./frontend_dist,
# откуда Dockerfile.frontend кладёт его в nginx уже на прод-сервере без сборки.
#
# Использование:
#   ./build_frontend.sh <API_URL> [DEPLOY_URL]
#
# Пример:
#   ./build_frontend.sh http://192.168.0.10
#
# ВАЖНО: API_URL — публичный адрес, по которому приложение открывают на проде
# (он же — точка входа для вебсокета Reflex через nginx, порт 80). Это значение
# вшивается в статику здесь и сейчас, поэтому при смене адреса прода фронт надо
# пересобрать этим скриптом заново.
# ============================================================================

API_URL="${1:-${API_URL:-http://localhost:8000}}"
DEPLOY_URL="${2:-${DEPLOY_URL:-$API_URL}}"

echo "[build_frontend] API_URL=$API_URL  DEPLOY_URL=$DEPLOY_URL"

API_URL="$API_URL" DEPLOY_URL="$DEPLOY_URL" \
    uv run reflex export --frontend-only --no-zip

rm -rf frontend_dist
mkdir -p frontend_dist
cp -R .web/build/client/. frontend_dist/

echo "[build_frontend] Готово. Статика в ./frontend_dist (API_URL=$API_URL)."
echo "[build_frontend] Перенесите проект вместе с frontend_dist на прод и:"
echo "                 docker compose up -d --build"
