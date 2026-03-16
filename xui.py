import json
import os
import time

import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv(".env")

BASE_URL = os.getenv("BASE_URL")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
INBOUND_ID = os.getenv("INBOUND_ID")
DAYS_VALID = 90


def auth():
    """Auth in x-ui api."""
    session = requests.Session()
    login_data = {"username": USERNAME, "password": PASSWORD}
    resp = session.post(f"{BASE_URL}/login", data=login_data, verify=False)

    if resp.status_code != 200:
        print(resp)
        raise ValueError("Auth failed.")

    print("✅ Authorized...")
    return session


def add_xui_client(user_id: int, nickname: str, obfuscated_user: str):
    """Adding new x-ui client via api on https."""
    print(f"Adding new x-ui client {nickname}")
    session = auth()
    expiry_timestamp = int((time.time() + DAYS_VALID * 86400) * 1000)

    clients_json = {
        "clients": [
            {
                "id": obfuscated_user,
                "tgId": str(user_id),
                "email": f"{obfuscated_user}@vray",
                "enable": True,
                "limitIp": 0,
                "totalGB": 0,
                "expiryTime": expiry_timestamp,
            }
        ]
    }

    payload = {"id": int(INBOUND_ID), "settings": json.dumps(clients_json)}
    response = session.post(
        f"{BASE_URL}/panel/api/inbounds/addClient", json=payload, verify=False
    )

    print(f"Server response:\n{response.text}")

    if response.ok and response.json().get("success"):
        print("✅ Client successfully added!")
    else:
        print("❌ Client was not added.")


def get_client_info(email: str):
    """Get client info."""
    session = auth()
    response = session.get(
        f"{BASE_URL}/panel/api/inbounds/get/{INBOUND_ID}", verify=False
    )
    if response.status_code == 200:
        data = response.json()
        clients = json.loads(data["obj"]["settings"])["clients"]
        client = next((c for c in clients if c.get("email") == email), None)
        sub_id = client["subId"]
        print(sub_id)
        return sub_id
    return []


def get_client_info_by_email(email: str):
    """Get client info by email."""
    session = auth()
    response = session.get(
        f"{BASE_URL}/panel/api/inbounds/get/{INBOUND_ID}", verify=False
    )
    if response.status_code != 200:
        print(
            f"❌ Failed to retrieve clients. Server responded with code {response.status_code}."
        )
        return None
    data = response.json()
    clients = json.loads(data["obj"]["settings"])["clients"]
    client = next((c for c in clients if c.get("email") == email), None)
    return client


def delete_xui_client(email: str):
    """Delete x-ui client."""
    client = get_client_info_by_email(email)
    session = auth()
    client_uuid = client["id"]
    response = session.get(
        f"{BASE_URL}/panel/api/inbounds/{INBOUND_ID}/delClient/{client_uuid}",
        verify=False,
    )
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print(f"✅ Client with email {email} successfully deleted!")
        else:
            print(f"❌ Client with email {email} was not deleted.")
    else:
        print(
            f"❌ Failed to delete client with email {email}. "
            f"Server responded with status code {response.status_code}."
        )


def update_xui_client(email: str, period: int):
    """Update x-ui client period."""
    client = get_client_info_by_email(email)
    session = auth()
    client_uuid = client["id"]
    current_expiry = client["expiryTime"]
    new_expiry = current_expiry + period * 86400 * 1000

    settings_obj = {
        "clients": [
            {
                "id": client_uuid,
                "email": email,
                "tgId": client.get("tgId", ""),
                "expiryTime": new_expiry,
                "enable": True,
                "subId": client["subId"],
            }
        ]
    }

    update_data = {
        "id": int(INBOUND_ID),
        "settings": json.dumps(settings_obj, separators=(",", ":")),
    }
    response = session.post(
        f"{BASE_URL}/panel/api/inbounds/updateClient/{client_uuid}",
        json=update_data,
        verify=False,
    )
    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            print(f"✅ Client with email {email} successfully updated!")
        else:
            print(f"❌ Client with email {email} was not updated.")


if __name__ == "__main__":
    # add_xui_client(os.getenv("ADMIN"), "test_nick2", "test")
    # delete_xui_client("test@vray")
    # update_xui_client("test@vray", 30)
    get_client_info("test@vray")
