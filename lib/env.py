import os

from dotenv import load_dotenv

load_dotenv()


def getenv(name: str, default=None) -> str | None:
    return os.getenv(name, default)
