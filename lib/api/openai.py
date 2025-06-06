from openai import OpenAI

from lib.env import getenv

openai_client = OpenAI(
    api_key=getenv("OPENAI_API_KEY"),
    base_url=getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1"),
)

extra_headers = {
    "HTTP-Referer": "https://github.com/ckt1031/outlook-summarizer",  # Site URL for rankings on openrouter.ai.
    "X-Title": "Outlook Summarizer",  # Site title for rankings on openrouter.ai.
}
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
        extra_headers=extra_headers,
    )

    res = completion.choices[0].message

    if not res:
        raise ValueError("No schema response from the model")

    if res.refusal:
        raise Exception(f"OpenAI schema response refusal: {res.refusal}")

    # Type check the parsed response
    schema.model_validate(res.parsed)

    return res.parsed
