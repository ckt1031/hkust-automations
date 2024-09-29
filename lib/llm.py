import os

import dotenv
from openai import OpenAI

dotenv.load_dotenv()


class LLM:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base_url = os.getenv(
            "OPENAI_API_BASE_URL", "https://api.openai.com/v1"
        )
        self.model = os.getenv("OPENAI_API_MODEL", "gpt-4o-mini")

        # Throw an error if the API key is not provided
        if self.api_key is None:
            raise ValueError(
                "OpenAI API key is not provided in the environment variables"
            )

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base_url,
            default_headers={"User-Agent": "HKUSTAutomationScript/1.0"},
        )

    def complete(self, system_message: str, user_message: str) -> str:
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

        return content
