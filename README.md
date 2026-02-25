# vray_mirror_bot
Interactive telegram bot for automate VRAY clients.

Based on my previous repo https://github.com/feel2code/vpn_wireguard_mirror_bot

## Installation
```bash
git clone https://github.com/feel2code/vray_mirror_bot.git
cd vray_mirror_bot
pip install -r requirements.txt
```
## Configuration
```bash
cp env.template .env
```
Edit `.env` file and set the following variables:
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

## Run
```bash
python3 main.py
```

## Features
- [x] VRAY

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
