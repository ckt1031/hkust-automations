import tiktoken
from loguru import logger
from openai import OpenAI

from lib.constant import HTTP_CLIENT_HEADERS
from lib.env import OPENAI_API_BASE_URL, OPENAI_API_KEY, OPENAI_API_MODEL


class LLM:
    def __init__(self):
        self.api_key = OPENAI_API_KEY

        # Throw an error if the API key is not provided
        if self.api_key is None:
            raise EnvironmentError(
                "OpenAI API key (OPENAI_API_KEY) is not provided in the environment variables"
            )

        self.api_base_url = OPENAI_API_BASE_URL
        self.model = OPENAI_API_MODEL

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base_url,
            default_headers=HTTP_CLIENT_HEADERS,
        )

    def get_token(self, content: str):
        encoding = tiktoken.get_encoding("o200k_base")

        token = encoding.encode(content)

        return len(token)

    def run_chat_completion(self, system_message: str, user_message: str) -> str:
        token = self.get_token(system_message + user_message)

        logger.info(f"Calling LLM model: {self.model}, token: {token}")

        chat_completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
        )

        content = chat_completion.choices[0].message.content

        if content is None:
            raise ValueError("OpenAI API did not return any content")

        token = self.get_token(content)

        logger.success(f"LLM model returned content with token: {token}")

        return content
