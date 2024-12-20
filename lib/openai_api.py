from dotenv import load_dotenv
from loguru import logger
from openai import OpenAI

from lib.env import getenv

load_dotenv()


def generate_chat_completion(system_message: str, user_message: str) -> str:
    client = OpenAI(
        api_key=getenv("OPENAI_API_KEY"),
        base_url=getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1"),
    )

    model = getenv("OPENAI_API_MODEL", "gpt-4o-mini")

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        stream=False,
        model=model,
        temperature=0.3,
    )

    content = chat_completion.choices[0].message.content

    if content is None:
        raise ValueError("OpenAI API did not return any content")

    logger.info(f"Called OpenAI API with model: {model}")

    return content
