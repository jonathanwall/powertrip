import logging
import os

import asyncpraw
import discord

from modqueue import stream

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(module)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Powertrip(discord.Bot):
    def __init__(self):
        discord.Bot.__init__(self)
        self.reddit = asyncpraw.Reddit()

    async def on_error(self, event, *args, **kwargs):
        log.info("on_error")
        return await super().on_error(event, *args, **kwargs)

    async def on_connect(self):
        log.info("on_connect")

    async def on_ready(self):
        log.info("on_ready")

    async def on_interaction(self, interaction):
        # log.info("on_interaction")
        pass

    async def on_disconnect(self):
        # log.info("on_disconnect")
        pass

    async def on_resumed(self):
        # log.info("on_resumed")
        pass


def main():
    pt = Powertrip()
    pt.add_cog(stream.ModQueueStream(pt))
    pt.run(os.environ["pt_token"])


if __name__ == "__main__":
    main()
