import logging
import os

import asyncpraw
import discord

from modqueue import stream

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(module)s: %(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


class Powertrip(discord.Bot):
    def __init__(self):
        discord.Bot.__init__(self)
        self.reddit = asyncpraw.Reddit()

    async def on_error(self, event, *args, **kwargs):
        log.error("on_error")
        return await super().on_error(event, *args, **kwargs)


def main():
    pt = Powertrip()
    pt.add_cog(stream.ModQueueStream(pt))
    pt.run(os.environ["pt_token"])


if __name__ == "__main__":
    main()
