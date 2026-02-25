#!/bin/bash
# Should be addded to cron
path=/root/vpn_wireguard_mirror_bot
cd $path
source venv/bin/activate
python revoke_checks.py
