import os

import uvloop
from asyncpraw import Reddit
from discord import Bot

from powertrip import PowerTrip


def main():
    uvloop.install()

    reddit = Reddit()
    bot = Bot(description="PowerTrip: discord + reddit moderation helper")
    bot.add_cog(PowerTrip(bot, reddit))
    bot.run(os.environ["pt_token"])


if __name__ == "__main__":
    main()
