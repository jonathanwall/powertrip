import logging
import os

import asyncpraw
import discord

from modqueue import stream

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

logging.getLogger("discord").setLevel(logging.WARN)
logging.getLogger("asyncpraw").setLevel(logging.WARN)
logging.getLogger("asyncprawcore").setLevel(logging.WARN)


class Powertrip(discord.Bot):
    def __init__(self):
        discord.Bot.__init__(self)
        self.reddit = asyncpraw.Reddit()

    def run(self, token=None):
        if token is None:
            token = os.environ["pt_token"]
        self.add_cog(stream.ModQueueStream(self))
        super().run(token)

    async def on_error(self, event, *args, **kwargs):
        log.info("on_error")
        return await super().on_error(event, *args, **kwargs)

    async def on_ready(self):
        log.info("on_ready")

    async def on_resumed(self):
        log.info("on_resumed")

    async def on_connect(self):
        log.info("on_connect")

    async def on_disconnect(self):
        log.info("on_disconnect")


def main():
    pt = Powertrip()
    pt.run()


if __name__ == "__main__":
    main()
