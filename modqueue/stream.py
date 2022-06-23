import asyncio
import logging
import os

import discord
from discord import Bot
from discord.ext import commands, tasks

from .embed import Embed
from .view import View

log = logging.getLogger(__name__)


class ModQueueStream(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.stream.start()

    @tasks.loop(seconds=60)
    async def stream(self) -> None:
        reddit_queue = {}
        try:
            subreddit = await self.bot.reddit.subreddit("mod")
            async for item in subreddit.mod.modqueue():
                if item.author is None:
                    await item.mod.remove(mod_note="Redditor is deleted or shadowbanned")
                else:
                    reddit_queue[item.id] = item
        except Exception as e:
            log.error(f"reddit error: {e.__class__.__name__}: {e}")
            return

        discord_queue = {}
        try:
            channel = self.bot.get_channel(int(os.environ["pt_queue_channel"]))
            async for message in channel.history():
                if message.author == self.bot.user:
                    try:
                        discord_queue[message.embeds[0].footer.text] = message
                    except IndexError:
                        pass
        except Exception as e:
            log.error(f"discord error: {e.__class__.__name__}: {e}")
            return

        for item_id in discord_queue:
            if item_id in reddit_queue:
                del reddit_queue[item_id]
            else:
                await discord_queue[item_id].delete(delay=0)

        for item in reversed(list(reddit_queue.values())):
            await item.author.load()
            await channel.send(embed=Embed(item), view=View(item))

    # Called before the loop starts running.
    @stream.before_loop
    async def before_stream(self) -> None:
        log.info("before_stream")
        await self.bot.wait_until_ready()

        try:
            channel = self.bot.get_channel(int(os.environ["pt_queue_channel"]))
            await channel.purge()
        except Exception as e:
            log.error(f"error purging queue channel:\n{e.__class__}: {e}")
            self.sleep_and_restart()
        else:
            activity = discord.Activity(type=discord.ActivityType.watching, name="reddit.")
            await self.bot.change_presence(activity=activity)

    # Called after the loop finishes running.
    @stream.after_loop
    async def after_stream(self) -> None:
        log.info("after_stream")
        if self.stream.is_being_cancelled():
            log.info("is_being_cancelled")
            return

        await self.bot.change_presence()
        await self.sleep_and_restart()

    # Called if the task encounters an unhandled exception.
    @stream.error
    async def error(self, error: Exception) -> None:
        log.error(f"stream.error: {error.__class__.__name__}: {error}")

    async def sleep_and_restart(self, sleep_seconds=None):
        sleep_seconds = 300 if sleep_seconds is None else sleep_seconds
        log.info(f"sleeping {sleep_seconds}")
        await asyncio.sleep(sleep_seconds)
        log.info("restarting stream")
        await self.stream.restart()
