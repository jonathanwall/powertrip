import os

from asyncpraw import Reddit
from discord import Bot

from . import streams


class Powertrip(Bot):
    def __init__(self):
        Bot.__init__(self)
        self.reddit = Reddit()
        self.add_cog(streams.ModQueue(self))

    def run(self, token=None):
        if token is None:
            token = os.environ["pt_token"]
        super().run(token)
