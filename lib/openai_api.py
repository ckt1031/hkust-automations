from dotenv import load_dotenv
from loguru import logger
from openai import OpenAI

from lib.env import getenv

load_dotenv()

client = OpenAI(
    api_key=getenv("OPENAI_API_KEY"),
    base_url=getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1"),
)

model = getenv("OPENAI_API_MODEL", "gpt-4o-mini")


def generate_schema(system_message: str, user_message: str, schema):
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_message.strip()},
            {"role": "user", "content": user_message.strip()},
        ],
        response_format=schema,
    )

    res = completion.choices[0].message

    if not res:
        raise ValueError("No schema response from the model")

    if res.refusal:
        raise Exception(f"OpenAI chat completion refusal: {res.refusal}")

    return res.parsed


def generate_chat_completion(system_message: str, user_message: str) -> str:
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_message.strip()},
            {"role": "user", "content": user_message.strip()},
        ],
        stream=False,
        model=model,
    )

    content = chat_completion.choices[0].message.content

    if content is None:
        raise ValueError("OpenAI API did not return any content")

    logger.debug(f"Called OpenAI API with model: {model}")

    return content
