import os

from dotenv import load_dotenv

load_dotenv()


def getenv(name: str, default=None, required=True) -> str | None:
    value = os.getenv(name, default)

    # Raise an error if the environment variable is required but not set
    if required and not value:
        raise ValueError(f"Environment variable {name} is required")

    return os.getenv(name, default)
