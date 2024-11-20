def read_email_system_prompt():
    with open("prompts/email-summarize.txt", "r") as f:
        return f.read()


def read_news_summary_system_prompt():
    with open("prompts/news.txt", "r") as f:
        return f.read()
