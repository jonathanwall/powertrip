import asyncio
import logging
import os

import asyncprawcore
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
        discord_queue = {}
        try:
            channel = self.bot.get_channel(int(os.environ["pt_queue_channel"]))
            async for message in channel.history():
                if message.author == self.bot.user:
                    try:
                        discord_queue[message.embeds[0].footer.text] = message
                    except IndexError:
                        pass
        except discord.DiscordServerError:
            return
        except Exception as e:
            log.error(f"discord error: {e. __class__.__name__}: {e}")
            return

        reddit_queue = {}
        try:
            subreddit = await self.bot.reddit.subreddit("mod")
            async for item in subreddit.mod.modqueue():
                if item.author is None:
                    await item.mod.remove()
                else:
                    reddit_queue[item.id] = item
        except asyncprawcore.exceptions.ServerError:
            return
        except Exception as e:
            log.error(f"reddit error: {e.__class__.__name__}: {e}")
            return

        for item in discord_queue:
            if item in reddit_queue:
                del reddit_queue[item]
            else:
                await discord_queue[item].delete(delay=0)

        for item in reversed(list(reddit_queue.values())):
            await item.author.load()
            await channel.send(embed=Embed(item), view=View(item))

    @stream.before_loop
    async def before_stream(self) -> None:
        await self.bot.wait_until_ready()
        try:
            channel = self.bot.get_channel(int(os.environ["pt_queue_channel"]))
        except KeyError:
            log.critical("Enviroment variable pt_queue_channel is not set.")
            os._exit(0)
        try:
            await channel.purge()
        except discord.HTTPException:
            log.error("discord.HTTPException while starting stream.")
            await self.sleep_and_restart()
        else:
            activity = discord.Activity(type=discord.ActivityType.watching, name="reddit.")
            await self.bot.change_presence(activity=activity)

    @stream.after_loop
    async def after_stream(self) -> None:
        if self.stream.is_being_cancelled():
            return
        await self.sleep_and_restart()

    # Called if the task encounters an unhandled exception.
    @stream.error
    async def error(self, error: Exception) -> None:
        log.error(
            f"An unhandled error has occured in the modqueue stream: {error.__class__.__name__}: {error}"
        )
        await self.sleep_and_restart()

    async def sleep_and_restart(self, sleep_seconds: int = None) -> None:
        sleep_seconds = 300 if sleep_seconds is None else sleep_seconds
        await self.bot.change_presence(status=discord.Status.idle)
        await asyncio.sleep(sleep_seconds)
        self.stream.restart()
