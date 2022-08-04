import logging
import os

import asyncpraw
import discord

from modqueue import stream

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(module)s: %(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


class Powertrip(discord.Bot):
    """The main Powertrip class."""

    def __init__(self):
        """Inits Powertrip."""
        discord.Bot.__init__(self)
        self.reddit = asyncpraw.Reddit(
            username=os.environ["PT_REDDIT_USERNAME"],
            password=os.environ["PT_REDDIT_PASSWORD"],
            client_id=os.environ["PT_REDDIT_CLIENT_ID"],
            client_secret=os.environ["PT_REDDIT_CLIENT_SECRET"],
            user_agent=f"Powertrip by u/walljonathan",
        )

    async def on_error(self, event, *args, **kwargs):
        """Override of the default error handler."""
        log.error("on_error")
        return await super().on_error(event, *args, **kwargs)


def main() -> None:
    """Run Powertrip."""
    pt = Powertrip()
    pt.add_cog(stream.ModQueueStream(pt))
    pt.run(os.environ["PT_DISCORD_TOKEN"])


if __name__ == "__main__":
    main()
