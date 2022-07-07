import logging
import os

import asyncpraw
import discord

from modqueue import stream

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(module)s: %(funcName)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("discord").setLevel(logging.ERROR)
logging.getLogger("asyncpraw").setLevel(logging.ERROR)

log = logging.getLogger(__name__)


class Powertrip(discord.Bot):
    def __init__(self):
        discord.Bot.__init__(self)
        self.reddit = asyncpraw.Reddit()

    async def on_error(self, event, *args, **kwargs):
        log.debug("on_error")
        return await super().on_error(event, *args, **kwargs)

    async def on_connect(self):
        log.debug("on_connect")

    async def on_ready(self):
        log.debug("on_ready")

    async def on_interaction(self, interaction):
        log.debug("on_interaction")
        pass

    async def on_disconnect(self):
        log.debug("on_disconnect")
        pass

    async def on_resumed(self):
        log.debug("on_resumed")
        pass


def main():
    try:
        import uvloop
    except ImportError:
        pass
    else:
        uvloop.install()
    pt = Powertrip()
    pt.add_cog(stream.ModQueueStream(pt))
    pt.run(os.environ["pt_token"])


if __name__ == "__main__":
    main()
