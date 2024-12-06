import httpx
from loguru import logger

from lib.constant import HTTP_CLIENT_HEADERS
from lib.env import OPENAI_API_BASE_URL, OPENAI_API_KEY, OPENAI_API_MODEL


def llm_generate(system_message: str, user_message: str) -> str:
    length = len(system_message + user_message)

    logger.info(f"Calling LLM model: {OPENAI_API_MODEL}, length: {length}")

    body = {
        "model": OPENAI_API_MODEL,
        "temperature": 0.3,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
    }

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    headers.update(HTTP_CLIENT_HEADERS)

    response = httpx.post(
        f"{OPENAI_API_BASE_URL}/chat/completions",
        headers=headers,
        json=body,
        timeout=60,
    )

    data = response.json()

    content: str | None = data["choices"][0]["message"]["content"]

    if content is None:
        raise ValueError("OpenAI API did not return any content")

    length = len(content)

    logger.success(f"LLM model returned content with length: {length}")

    return content
