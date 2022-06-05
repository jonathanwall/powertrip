import logging
import os

import discord
import asyncpraw
from modqueue import stream

logging.basicConfig(level=logging.WARN)
log = logging.getLogger(__name__)


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
