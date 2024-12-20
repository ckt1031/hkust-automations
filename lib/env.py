import os

from dotenv import load_dotenv

load_dotenv()


def getenv(name: str, default=None) -> str | None:
    try:
        return os.getenv(name, default)
    except KeyError:
        raise KeyError(f"Environment variable {name} not set")
