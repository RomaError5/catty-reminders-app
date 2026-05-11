#!/bin/bash
set -e
# Скрипт должен находиться в корне репозитория
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

# Активация виртуального окружения
if [ -d "venv" ]; then
    source venv/bin/activate
else
    python3 -m venv venv
    source venv/bin/activate
fi

# Установка зависимостей
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# Запуск тестов (предполагается, что тесты не требуют работающего HTTP-сервера)
if [ -d "tests" ]; then
    pytest tests --maxfail=1 --disable-warnings -q
else
    echo "No tests found, skipping"
fi