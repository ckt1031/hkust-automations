from functools import lru_cache


@lru_cache(maxsize=1)
def read_email_system_prompt():
    with open("prompts/email-summarize.txt", "r") as f:
        return f.read()


@lru_cache(maxsize=1)
def read_summary_system_prompt():
    with open("prompts/summary.txt", "r") as f:
        return f.read()
