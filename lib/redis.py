import asyncio
import os

import dotenv
import redis

dotenv.load_dotenv()


redis_connection_string = os.environ["REDIS_CONNECTION_STRING"]

redis_client = redis.from_url(redis_connection_string)


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
