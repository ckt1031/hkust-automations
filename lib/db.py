import asyncio
import hashlib
import os
from datetime import timezone

import dotenv
import redis
from dateutil import parser

dotenv.load_dotenv()


redis_connection_string = os.environ["REDIS_CONNECTION_STRING"]

redis_client = redis.from_url(redis_connection_string)


def hash_string_sha256(input_string: str):
    # Create a SHA-256 hash object
    sha256_hash = hashlib.sha256()

    # Update the hash object with the bytes of the input string
    sha256_hash.update(input_string.encode("utf-8"))

    # Get the hexadecimal representation of the hash
    return sha256_hash.hexdigest()


def get_ms(date: str):
    parsed_date = parser.parse(date)

    # Ensure parsed_date is timezone-aware
    if parsed_date.tzinfo is None:
        parsed_date = parsed_date.replace(tzinfo=timezone.utc)

    return parsed_date.timestamp()


def is_record_exist(key: str):
    # Awaitable
    value = redis_client.exists(key)

    return value


async def get_all_unexpected_sender():
    data: set = set()
    action = redis_client.smembers("unexpected_email_senders")

    if asyncio.iscoroutine(action) or isinstance(action, asyncio.Task):
        data = await action

    return data


def set_redis_boolean_value(key: str, value: bool, expire_time: int = -1):
    # 0 for False, 1 for True
    redis_client.set(key, int(value), ex=None if expire_time == -1 else expire_time)


def set_redis_number_value(key: str, value: int, expire_time: int = -1):
    redis_client.set(key, value, ex=None if expire_time == -1 else expire_time)
