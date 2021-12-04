import os

import uvloop
from discord import Bot

from powertrip import PowerTrip


def main():
    uvloop.install()

    bot = Bot(description="PowerTrip: discord + reddit moderation helper")
    bot.add_cog(PowerTrip(bot))
    bot.run(os.environ["pt_token"])


if __name__ == "__main__":
    main()
