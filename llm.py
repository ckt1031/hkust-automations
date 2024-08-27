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
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base_url,
        )

    def complete(self, system_message: str, user_message: str) -> str:
        chat_completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
        )

        return chat_completion.choices[0].message.content
