import json
import webbrowser

import requests
from rich.console import Console

import lib.env as env

console = Console()

# https://learn.microsoft.com/en-us/graph/permissions-reference


def run_browser_authorization():
    url = f"https://login.microsoftonline.com/{env.MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize"

    querystring = {
        "code_challenge": env.MICROSOFT_CODE_CHALLENGE,
        "code_challenge_method": "S256",
        "prompt": "login",
        "redirect_uri": "https://jwt.ms",
        "response_mode": "query",
        "client_id": env.MICROSOFT_CLIENT_ID,
        "response_type": "code",
        "state": "00000",  # random state
        "scope": "profile openid offline_access email https://graph.microsoft.com/user.read https://graph.microsoft.com/mail.read",
    }

    webbrowser.open(url + "?" + "&".join([f"{k}={v}" for k, v in querystring.items()]))


def get_private_graph_token(full=False):
    url = (
        f"https://login.microsoftonline.com/{env.MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
    )

    payload = {
        "grant_type": (
            "refresh_token" if env.MICROSOFT_TENANT_ID else "authorization_code"
        ),
        "client_id": env.MICROSOFT_CLIENT_ID,
        "scope": "profile openid offline_access email https://graph.microsoft.com/user.read https://graph.microsoft.com/mail.read",
        "code": env.MICROSOFT_CODE,
        "redirect_uri": "https://jwt.ms",
        "code_verifier": env.MICROSOFT_CODE_VERIFIER,
        "client_secret": env.MICROSOFT_CLIENT_SECRET,
        "refresh_token": env.MICROSOFT_REFRESH_TOKEN,
    }

    response = requests.post(url, data=payload)

    return (
        json.loads(response.text) if full else json.loads(response.text)["access_token"]
    )
