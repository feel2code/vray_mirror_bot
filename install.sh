#!/usr/bin/env bash

set -euo pipefail

REPO_DIR="vray_mirror_bot"
URL="https://github.com/feel2code/vray_mirror_bot.git"

echo "🚀 Устанавливаем vray_mirror_bot..."

if ! command -v git &> /dev/null; then
    echo "❌ Git не установлен. Установите git и повторите." >&2
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен. Установите python3 и повторите." >&2
    exit 1
fi

if [ -d "$REPO_DIR" ]; then
    echo "🗑️  Удаляем существующую директорию $REPO_DIR"
    rm -rf "$REPO_DIR"
fi

echo "📥 Клонируем репозиторий..."
git clone "$URL" "$REPO_DIR"
cd "$REPO_DIR"
echo "🐍 Создаем виртуальное окружение..."
python3 -m venv venv
source venv/bin/activate
echo "📦 Обновляем pip..."
pip install --upgrade pip
echo "📦 Устанавливаем зависимости..."
pip install -r requirements.txt
echo "✅ Установка завершена!"
echo "-----------------------"
echo "📂 Проект установлен в директории: $PWD"
echo "🔧 Для запуска активируйте окружение: source venv/bin/activate"
echo "🐍 И запустите: python main.py"
