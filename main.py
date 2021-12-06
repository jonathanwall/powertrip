import os

from asyncpraw import Reddit
from discord import Bot

from powertrip import PowerTrip


def main():
    try:
        import uvloop
    except ImportError:
        pass
    else:
        uvloop.install()

    bot = Bot(description="PowerTrip: discord + reddit moderation helper")
    reddit = Reddit()

    bot.add_cog(PowerTrip(bot, reddit))
    bot.run(os.environ["pt_token"])


if __name__ == "__main__":
    main()
