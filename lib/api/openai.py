from loguru import logger
from openai import OpenAI

from lib.env import getenv

openai_client = OpenAI(
    api_key=getenv("OPENAI_API_KEY"),
    base_url=getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1"),
    extra_headers={
        "HTTP-Referer": "HKUST Automations",  # Site URL for rankings on openrouter.ai.
        "X-Title": "https://github.com/ckt1031/hkust-automations",  # Site title for rankings on openrouter.ai.
    },
)

model = getenv("OPENAI_API_MODEL", "gpt-4o-mini")


def generate_schema(system_message: str, user_message: str, schema):
    completion = openai_client.beta.chat.completions.parse(
        model=model,
        messages=[
            {"role": "system", "content": system_message.strip()},
            {"role": "user", "content": user_message.strip()},
        ],
        response_format=schema,
        temperature=0.5,
    )

    res = completion.choices[0].message

    if not res:
        raise ValueError("No schema response from the model")

    if res.refusal:
        raise Exception(f"OpenAI schema response refusal: {res.refusal}")

    # Type check the parsed response
    schema.model_validate(res.parsed)

    return res.parsed


def generate_chat_completion(system_message: str, user_message: str) -> str:
    chat_completion = openai_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_message.strip()},
            {"role": "user", "content": user_message.strip()},
        ],
        stream=False,
        model=model,
        temperature=0.5,
    )

    content = chat_completion.choices[0].message.content

    if content is None:
        raise ValueError("OpenAI API did not return any content")

    logger.debug(f"Called OpenAI API with model: {model}")

    return content
