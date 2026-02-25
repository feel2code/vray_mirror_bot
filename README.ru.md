# vray_mirror_bot

[English](README.md) | [Русский](README.ru.md)

Интерактивный телеграм бот для автоматизации клиентов vray.

Основано на моем предыдущем репозитории https://github.com/feel2code/vpn_wireguard_mirror_bot

## Установка одним кликом
```bash
curl -fsSL https://raw.githubusercontent.com/feel2code/vray_mirror_bot/main/install.sh | bash
```
## Конфигурация
```bash
cp env.template .env
```
Замените значения в файле `.env` на свои.
```bash
BOT_TOKEN=
SERVICE_NAME=
ADMIN=
FS_USER=
DB_NAME=
DEMO_REGIME=1
HOST_URL=
VRAY_90=
BASE_URL=
USERNAME=
PASSWORD=
INBOUND_ID=
```

## Запуск
```bash
source venv/bin/activate; python3 main.py
```

## Features
- [x] VRAY

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
