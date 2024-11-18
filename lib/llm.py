import os

import dotenv
import tiktoken
from loguru import logger
from openai import OpenAI

dotenv.load_dotenv()


class LLM:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

        # Throw an error if the API key is not provided
        if self.api_key is None:
            raise ValueError(
                "OpenAI API key (OPENAI_API_KEY) is not provided in the environment variables"
            )

        self.api_base_url = os.getenv(
            "OPENAI_API_BASE_URL", "https://api.openai.com/v1"
        )
        self.model = os.getenv("OPENAI_API_MODEL", "gpt-4o-mini")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base_url,
            default_headers={"User-Agent": "HKUST-Push/1.0"},
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
