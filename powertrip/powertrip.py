import os

from asyncpraw import Reddit
from discord import Bot

class Powertrip(Bot):
    def __init__(self):
        Bot.__init__(self)
        self.reddit = Reddit()

    def run(self, token=None):
        if token is None:
            token = os.environ["pt_token"]
        super().run(token)