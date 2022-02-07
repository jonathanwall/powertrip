import datetime
import os
from asyncio import sleep
from venv import create

import discord
from discord.ext import commands, tasks

from .embed import create_embed
from .view import create_view


class ModQueueStream(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel = None
        self.subreddit = None
        self.stream.start()

    @tasks.loop(seconds=5)
    async def stream(self):
        queue = {}
        try:
            async for item in self.subreddit.mod.modqueue():
                queue[item.id] = item
        except Exception as e:
            await self.wait_and_restart(e)

        channel = {}
        async for message in self.channel.history():
            if message.author == self.bot.user:
                channel[message.embeds[0].footer.text] = message

        if channel.keys() == queue.keys():
            return

        for item_id in channel:
            if item_id in queue:
                del queue[item_id]
            else:
                try:
                    await channel[item_id].delete()
                except discord.NotFound:
                    pass

        for item in reversed(list(queue.values())):
            embed = await create_embed(item)
            view = await create_view(item)
            await self.channel.send(embed=embed, view=view)

    @stream.before_loop
    async def before_stream(self):
        await self.bot.wait_until_ready()

        self.subreddit = await self.bot.reddit.subreddit("mod")
        self.channel = self.bot.get_channel(int(os.environ["pt_queue_channel"]))

        await self.channel.purge()
        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="reddit."
            )
        )

    @stream.after_loop
    async def after_stream(self):
        if not self.stream.is_being_cancelled():
            await self.wait_and_restart()
        await self.channel.purge()
        await self.channel.send("The modqueue stream has stopped.")

    async def wait_and_restart(self, error=None):
        await self.channel.purge()
        if error is not None:
            message = f"The stream has encountered an error:\n`{error}`\nTrying again in 5 minutes."
        else:
            message = (
                f"The stream has encountered an error.\nTrying again in 5 minutes."
            )
        await self.channel.send(message)
        await sleep(300)
        self.stream.restart()
