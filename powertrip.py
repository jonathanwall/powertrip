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


def main():
    pt = Powertrip()
    pt.run()


if __name__ == "__main__":
    main()
