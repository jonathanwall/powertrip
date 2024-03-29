import logging
from datetime import datetime

import discord
from asyncpraw.models.reddit.comment import Comment
from asyncpraw.models.reddit.submission import Submission

log = logging.getLogger(__name__)


class Embed(discord.Embed):
    def __init__(self, item):
        super().__init__()
        self.color = discord.Color.red()
        self.timestamp = datetime.fromtimestamp(item.created_utc)
        self.set_footer(text=item.id)
        if isinstance(item, Comment):
            self.add_field(
                name="Comment",
                value=f"**[{item.body[:900]}]" + f"(https://www.reddit.com{item.permalink})**",
                inline=False,
            )
        if isinstance(item, Submission):
            self.add_field(
                name="Submission",
                value=f"**[{item.title}]" + f"(https://www.reddit.com{item.permalink})**",
                inline=False,
            )
            if item.selftext:
                selftext = (
                    f"[{item.selftext[:900]}]" + f"(https://www.reddit.com{item.permalink})"
                )
                self.add_field(name="Submission Text", value=selftext, inline=False)

            if item.url.endswith((".jpg", ".jpeg", ".gif", ".gifv", ".png", ".svg")):
                image_url = item.url
                self.set_image(url=item.url)
            elif "imgur.com" in item.url:
                image_url = item.url + ".jpg"
                self.set_image(url=image_url)
            elif hasattr(item, "media_metadata"):
                try:
                    image_url = list(item.media_metadata.values())[0]["s"]["u"]
                    self.set_image(url=image_url)
                except KeyError:
                    pass

        author_field_value = f"[{item.author}](https://www.reddit.com/u/{item.author})"
        if hasattr(item.author, "total_karma"):
            author_field_value += f" \n **Karma** {item.author.total_karma}"
        if hasattr(item.author, "created_utc"):
            author_field_value += f" \n **Created** {datetime.fromtimestamp(item.author.created_utc).strftime('%m/%d/%Y')}"
        self.add_field(
            name="Author",
            value=author_field_value,
            inline=False,
        )
        if item.user_reports or item.mod_reports:
            self.color = discord.Color.yellow()
            if item.user_reports:
                report = item.user_reports[0][0]
                self.add_field(name="User Report", value=report, inline=False)
            if item.mod_reports:
                mod_report = item.mod_reports[0][0]
                self.add_field(name="Mod Report", value=mod_report, inline=False)
