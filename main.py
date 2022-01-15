import os

from asyncpraw import Reddit
from discord import Bot

from powertrip import ModQueueStream


def main():
    bot = Bot(description="PowerTrip: discord + reddit moderation helper")
    reddit = Reddit()

    bot.add_cog(ModQueueStream(bot, reddit))
    bot.run(os.environ["pt_token"])


if __name__ == "__main__":
    main()
