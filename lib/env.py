import os

from dotenv import load_dotenv

load_dotenv()


class Environment:
    def get(name, default=None) -> str | None:
        try:
            return os.getenv(name, default)
        except KeyError:
            raise
