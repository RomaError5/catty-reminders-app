#!/usr/bin/env python3
"""
GitHub Webhook Receiver для автоматического развертывания приложения.
Ожидает push-события, обновляет код, запускает тесты и перезапускает сервис.
"""

import os
import sys
import json
import hmac
import hashlib
import subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.stdout.reconfigure(line_buffering=True)

# ========== Конфигурация через переменные окружения ==========
REPO_URL = os.environ.get('REPO_URL', 'https://github.com/RomaError5/catty-reminders-app.git')
APP_DIR = os.environ.get('APP_DIR', '/home/romaerror5/Desktop/devops/catty-reminders-app')
PORT = int(os.environ.get('WEBHOOK_PORT', 8080))
SERVICE_NAME = os.environ.get('SERVICE_NAME', 'app.service')
USE_SUDO = os.environ.get('USE_SUDO', 'true').lower() == 'true'

class WebhookHandler(BaseHTTPRequestHandler):
    """Обработчик HTTP запросов для GitHub Webhook"""

    def do_GET(self):
        """Страница статуса сервера"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>DevOps Webhook Server</title><meta charset="utf-8"></head>
        <body style="font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
            <h1>🚀 DevOps Webhook Receiver</h1>
            <p><strong>Статус:</strong> активен</p>
            <p><strong>Порт:</strong> {PORT}</p>
            <p><strong>Время запуска:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Репозиторий:</strong> {REPO_URL}</p>
            <p><strong>Рабочая директория:</strong> {APP_DIR}</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode('utf-8'))

    def do_POST(self):
        """Приём webhook от GitHub"""
        print(f"Headers: {self.headers}", flush=True)
        print(f"Event: {self.headers.get('X-GitHub-Event')}", flush=True)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        signature = self.headers.get('X-Hub-Signature-256', '')

        # Определяем тип события
        event_type = self.headers.get('X-GitHub-Event', '')
        if event_type != 'push':
            self._log(f"ℹ️  Игнорируем событие '{event_type}' (только push)")
            self.send_response(200)
            self.end_headers()
            return

        # Парсим payload
        try:
            payload = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            self._log("❌ Ошибка парсинга JSON")
            self.send_response(400)
            self.end_headers()
            return

        # Извлекаем ветку
        ref = payload.get('ref', '')
        if not ref.startswith('refs/heads/'):
            self._log(f"ℹ️  Не ветка: {ref}")
            self.send_response(200)
            self.end_headers()
            return
        branch = ref.replace('refs/heads/', '')

        # Логируем событие
        repo_name = payload.get('repository', {}).get('full_name', 'unknown')
        pusher = payload.get('pusher', {}).get('name', 'unknown')
        self._log(f"🔔 Push в {repo_name}:{branch} от {pusher}")

        # Запускаем процесс развертывания
        try:
            success = self._deploy(branch)
            if success:
                self._log("✅ Развертывание успешно завершено")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status":"success"}')
            else:
                self._log("❌ Развертывание не удалось")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b'{"status":"failed"}')
        except Exception as e:
            self._log(f"❌ Исключение при развертывании: {e}")
            self.send_response(500)
            self.end_headers()

    def _log(self, msg):
        """Вывод лога с временной меткой"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {msg}")

    def _deploy(self, branch):
        """Основная логика развертывания: клонирование/обновление, тесты, перезапуск"""
        self._log(f"🚀 Начинаем развертывание ветки '{branch}'")

        # 1. Клонируем или обновляем репозиторий
        if not os.path.isdir(os.path.join(APP_DIR, '.git')):
            self._log(f"Клонирование репозитория в {APP_DIR}")
            subprocess.run(['git', 'clone', REPO_URL, APP_DIR], check=True, capture_output=True)
        else:
            self._log("Обновление существующего репозитория")
            subprocess.run(['git', '-C', APP_DIR, 'fetch', 'origin'], check=True, capture_output=True)

        # Сбрасываем все локальные изменения (особенно .env)
        subprocess.run(['git', '-C', APP_DIR, 'reset', '--hard', 'HEAD'], check=True, capture_output=True)

        # Переключаемся на нужную ветку
        subprocess.run(['git', '-C', APP_DIR, 'checkout', branch], check=True, capture_output=True)
        subprocess.run(['git', '-C', APP_DIR, 'reset', '--hard', f'origin/{branch}'], check=True, capture_output=True)

        # Получаем текущий хеш коммита
        commit_hash = subprocess.check_output(['git', '-C', APP_DIR, 'rev-parse', 'HEAD'], text=True).strip()
        self._log(f"Текущий коммит: {commit_hash}")

        # 2. Запуск тестов (если есть скрипт test.sh)
        test_script = os.path.join(APP_DIR, 'test.sh')
        if os.path.exists(test_script):
            self._log("Запуск тестов...")
            try:
                # Передаём ветку как аргумент в test.sh
                subprocess.run([test_script, branch], cwd=APP_DIR, check=True, capture_output=True)
                self._log("✅ Тесты успешно пройдены")
            except subprocess.CalledProcessError as e:
                self._log(f"❌ Тесты не пройдены: код возврата {e.returncode}")
                self._log(e.stdout.decode())
                self._log(e.stderr.decode())
                return False
        else:
            self._log("⚠️  Нет test.sh, пропускаем тесты")

        # 3. Обновляем .env файл с новым DEPLOY_REF
        env_file = os.path.join(APP_DIR, '.env')
        with open(env_file, 'w') as f:
            f.write(f"DEPLOY_REF={commit_hash}\n")
        self._log("Обновлён .env файл")

        # 4. Перезапуск сервиса
        self._log(f"Перезапуск systemd сервиса {SERVICE_NAME}")
        cmd = ['systemctl', 'restart', SERVICE_NAME]
        if USE_SUDO:
            cmd = ['sudo'] + cmd
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            self._log("✅ Сервис перезапущен")
        except subprocess.CalledProcessError as e:
            self._log(f"❌ Не удалось перезапустить сервис: {e.stderr.decode()}")
            return False

        return True

def main():
    """Запуск HTTP сервера"""
    print(f"Запуск webhook-сервера на порту {PORT}")
    print(f"Репозиторий: {REPO_URL}")
    print(f"Рабочая директория: {APP_DIR}")
    print(f"Сервис: {SERVICE_NAME}")
    server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nОстановка сервера")
        server.shutdown()

if __name__ == '__main__':
    main()