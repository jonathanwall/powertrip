import asyncio
import logging
import os

import discord
from discord.ext import commands, tasks

from .embed import Embed
from .view import View

log = logging.getLogger(__name__)


class ModQueueStream(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stream.start()

    @tasks.loop(seconds=5)
    async def stream(self):
        reddit_queue = {}

        subreddit = await self.bot.reddit.subreddit("mod")

        async for item in subreddit.mod.modqueue():
            if item.author is None:
                await item.mod.remove(mod_note="Redditor is deleted or shadowbanned.")
            else:
                reddit_queue[item.id] = item

        discord_queue = {}

        channel = self.bot.get_channel(int(os.environ["pt_queue_channel"]))

        async for message in channel.history():
            if message.author == self.bot.user:
                try:
                    discord_queue[message.embeds[0].footer.text] = message
                except IndexError:
                    pass

        for item_id in discord_queue:
            if item_id in reddit_queue:
                del reddit_queue[item_id]
            else:
                await discord_queue[item_id].delete(delay=0)

        for item in reversed(list(reddit_queue.values())):
            await item.author.load()
            embed = Embed(item)
            view = View(item)
            await channel.send(embed=embed, view=view)

    @stream.before_loop
    async def before_stream(self):
        log.info("before_stream")
        await self.bot.wait_until_ready()

        channel = self.bot.get_channel(int(os.environ["pt_queue_channel"]))
        await channel.purge()

        watching = discord.Activity(type=discord.ActivityType.watching, name="reddit.")
        await self.bot.change_presence(activity=watching)

    @stream.after_loop
    async def after_stream(self):
        log.info("after_stream")
        await self.bot.change_presence()

    @stream.error
    async def error(self, error):
        log.info("error")
        log.error(error)

        await self.bot.change_presence()

        channel = self.bot.get_channel(int(os.environ["pt_queue_channel"]))

        await channel.purge()

        await channel.send(f"An error has occurred. Restarting in 5 minutes.")

        await asyncio.sleep(300)

        self.stream.restart()
