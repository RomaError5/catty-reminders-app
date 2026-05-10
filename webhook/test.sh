#!/bin/bash
set -e

APP_DIR="/home/romaerror5/Desktop/devops/catty-reminders-app"
VENV="$APP_DIR/venv"

echo "=== Запуск тестов проекта ветки $BRANCH==="

cd "$APP_DIR"

DEPLOY_REF="$(git rev-parse HEAD)"

echo "Текущий SHA ветки $BRANCH: $DEPLOY_REF"
echo "DEPLOY_REF=$DEPLOY_REF" > /home/romaerror5/Desktop/devops/catty-reminders-app/.env

if [ -f "requirements.txt" ]; then
    if [ ! -d "venv" ]; then
        echo "=== создание виртуального окружения $BRANCH ==="
        python3 -m venv venv
    fi
    echo "=== запуск виртуального окружения $BRANCH ==="
    source venv/bin/activate
    echo "=== установка зависимостей $BRANCH ==="
    pip install -r requirements.txt
fi

if [ -f "requirements.txt" ]; then
    echo "=== Установка зависимостей ==="
    pip install -r requirements.txt
fi

echo "Текущая директория: $(pwd)"
if [ -f "requirements.txt" ]; then
    if [ ! -d "venv" ]; then
        echo "=== создание виртуального окружения $BRANCH ==="
        python3 -m venv venv
    fi
    echo "=== запуск виртуального окружения $BRANCH ==="
    source venv/bin/activate
    echo "=== установка зависимостей $BRANCH ==="
    pip install -r requirements.txt
fi

echo "=== запуск приложения $BRANCH   !==="
sudo systemctl stop app.service
set -a
source "$APP_DIR/.env"
set +a
nohup "$APP_DIR/venv/bin/uvicorn" app.main:app --reload --host 0.0.0.0 --port 8181 > /dev/null 2>&1 &
APP_PID=$!

sleep 3

export PYTHONPATH=/home/romaerror5/Desktop/devops/catty-reminders-app:$PYTHONPATH
echo "=== Выполняем тесты из папки tests ==="
PLAYWRIGHT_BROWSERS_PATH=/home/romaerror5/Desktop/devops/.cache/ms-playwright pytest tests --maxfail=1 --disable-warnings -q
RESULT=$?
kill $APP_PID

exit $RESULT