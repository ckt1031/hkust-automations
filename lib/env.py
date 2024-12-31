import os
from functools import cache

from dotenv import load_dotenv

load_dotenv()


@cache
def getenv(name: str, default=None) -> str | None:
    try:
        return os.getenv(name, default)
    except KeyError:
        raise KeyError(f"Environment variable {name} not set")
