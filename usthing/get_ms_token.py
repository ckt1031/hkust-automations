import json
import os
import time
import webbrowser

import pkce
import requests
from dotenv import load_dotenv
from rich.console import Console

console = Console()

load_dotenv()

code_verifier = os.getenv("MS_CODE_VERIFIER", pkce.generate_code_verifier(length=74))
code_challenge = pkce.get_code_challenge(code_verifier)


def get_login():
    url = "https://login.microsoftonline.com/c917f3e2-9322-4926-9bb3-daca730413ca/oauth2/v2.0/authorize"
    querystring = {
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "prompt": "login",
        "redirect_uri": "usthing://oauth-login",
        "client_id": "b4bc4b9a-7162-44c5-bb50-fe935dce1f5a",
        "response_type": "code",
        "state": "JSziTmr3GZ",
        "scope": "openid%20offline_access",
    }

    console.print("Opening browser for login", style="green")
    console.print(f"Your Code Verifier: {code_verifier}", style="blue")
    console.print(f"Your Code Challenge: {code_challenge}", style="blue")

    webbrowser.open(url + "?" + "&".join([f"{k}={v}" for k, v in querystring.items()]))


def save_access_token_from_refresh(body: dict):
    with open("./access_token.json", "w") as f:
        # Write the expiry time to the file
        expire_ms = int(body["expires_in"]) * 1000 + int(time.time() * 1000)
        body["expire_ms"] = expire_ms
        # Write all data into the file including the expiry time
        f.write(json.dumps(body))


def read_access_token() -> str | None:
    try:
        with open("./access_token.json", "r") as f:
            data = json.loads(f.read())
            if data["expire_ms"] > int(time.time() * 1000):
                console.print("Retrieved Access Token from file")

                return data["access_token"]
            else:
                return None
    except FileNotFoundError:
        return None


def get_access_token() -> str:
    access_token = read_access_token()

    if access_token:
        return access_token

    url = "https://login.microsoftonline.com/c917f3e2-9322-4926-9bb3-daca730413ca/oauth2/v2.0/token"

    code = os.getenv("MS_CODE")
    refresh_token = os.getenv("MS_REFRESH_TOKEN")

    headers = {
        # ":authority": "login.microsoftonline.com",
        # ":method": "POST",
        # ":path": "/c917f3e2-9322-4926-9bb3-daca730413ca/oauth2/v2.0/token",
        # ":scheme": "https",
        # "cookie": "fpc=AqzkYpVZD-9Eham7ENn6didKhjmVAQAAAKHBiN4OAAAA",
        "accept": "application/json, text/javascript; q=0.01",
        "content-type": "application/x-www-form-urlencoded",
        "user-agent": "USThing/113 CFNetwork/1568.100.1 Darwin/24.0.0",
        "accept-language": "en-GB,en;q=0.9",
        "content-length": "1204",
        "accept-encoding": "gzip, deflate, br",
    }
    data = {
        "grant_type": "refresh_token" if refresh_token else "authorization_code",
        "client_id": "b4bc4b9a-7162-44c5-bb50-fe935dce1f5a",
        "code_verifier": code_verifier,
        "redirect_uri": "usthing://oauth-login",
        "code": code,
        "refresh_token": refresh_token,
    }
    response = requests.post(url, headers=headers, data=data, timeout=10)

    if response.status_code > 300:
        print(response.status_code)
        print(response.text)
        raise ValueError("Error when generating Access Token!")

    save_access_token_from_refresh(response.json())

    console.print("Generated Access Token from MS", style="green")

    return json.loads(response.text)
