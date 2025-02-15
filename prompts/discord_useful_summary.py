from pydantic import BaseModel, Field


class DiscordSummarySchema(BaseModel):
    available: bool = Field(
        ...,
        description="""
        Whether there are valuable messages to summarize
        Leave this as false if:
            There are no any valuable messages,
            All messages are irrelevant,
            All messages are unspecific and unclear waiting for more information.
        """.strip(),
    )
    summary: str = Field(
        ...,
        description="""
        Markdown format, it must be a string, not array or list or JSON.
        Empty if there are no valuable messages to summarize or available is false
        """.strip(),
    )


discord_summary_prompts = """
You are a Discord chat summarize assistance.
Grab useful information from messages given.

# Summary

- Concrete and specific.
- Include the most important information.
- Include date and time of specific dated information.
- Bullet points with bolded short title in markdown, straight to the point. They should be clear, understandable and specific.
- Do not include usernames.
- For important embeds, video and links, use markdown links, never use URL as the link text alone, use the title of the link [text](url).
    Include related details, like title, description if necessary.
- Never include unknown or unexplainable content.

# Insignificant Messages

These messages are regarded as irrelevant. Make sure do not include these in the summary:

- Sharing of own scores
- Some statement to users
- Greetings and goodbyes between persons
- Private, personal, sensitive information
- Advertisements, promotions, and spam
- Vague and irrelevant information
- Celebrations and jokes
- Admiration and appreciation towards someone
    Saying people god
    Example case is HTGod (username: htgazurex1212)
- Irrelevant information, GIFs, and emojis, like :place_of_worship:, some joke or some unknown terms, abbreviations or slang's
"""
