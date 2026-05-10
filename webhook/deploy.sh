#!/bin/bash
set -e

BRANCH=$1
REPO_URL="git@github.com:RomaError5/catty-reminders-app"
APP_DIR="/home/romaerror5/Desktop/devops/catty-reminders-app"

echo "=== DEPLOY ветки $BRANCH ==="

if [ ! -d "$APP_DIR/.git" ]; then
    echo "Первый запуск — клонирование"
    git clone $REPO_URL $APP_DIR
fi

cd $APP_DIR

git fetch origin

git checkout -B $BRANCH origin/$BRANCH

git reset --hard origin/$BRANCH

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

echo "=== запуск приложения $BRANCH ==="
sudo systemctl restart app.service