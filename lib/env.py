import os

import pkce
from dotenv import load_dotenv

load_dotenv()

MICROSOFT_CODE_VERIFIER = os.getenv(
    "MICROSOFT_CODE_VERIFIER", pkce.generate_code_verifier(length=74)
)
MICROSOFT_CODE_CHALLENGE = pkce.get_code_challenge(MICROSOFT_CODE_VERIFIER)
MICROSOFT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID")
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
MICROSOFT_REFRESH_TOKEN = os.getenv("MICROSOFT_REFRESH_TOKEN")
MICROSOFT_CODE = os.getenv("MICROSOFT_CODE")
