import os

import discord
from asyncpraw import Reddit
from discord.ext import commands, tasks

from .helpers import get_new_items, send_item_to_channel


class PowerTrip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel = None
        self.reddit = Reddit()
        self.subreddit = None
        self.stream.start()

    @tasks.loop(seconds=60)
    async def stream(self):
        new_items = await get_new_items()

        for item in new_items:
            await send_item_to_channel(new_items[item])

    @stream.before_loop
    async def before_stream(self):
        await self.bot.wait_until_ready()

        self.subreddit = await self.reddit.subreddit("mod")
        self.channel = self.bot.get_channel(int(os.environ["pt_queue_channel"]))

        await self.channel.purge()
        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="reddit.")
        )

    @stream.after_loop
    async def after_stream(self):
        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="nothing. I'm broken."
            )
        )
        if not self.stream.is_being_cancelled():
            self.stream.restart()
