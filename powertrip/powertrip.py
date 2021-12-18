import datetime
import os
from asyncio import sleep

import discord
from asyncpraw.models.reddit import comment, submission
from discord import embeds
from discord.errors import NotFound
from discord.ext import commands, tasks

from .view import View


class PowerTrip(commands.Cog):
    def __init__(self, bot, reddit):
        self.bot = bot
        self.reddit = reddit
        self.channel = None
        self.subreddit = None
        self.stream.start()

    @tasks.loop(seconds=60)
    async def stream(self):
        new_items = await self.get_new_items()
        for item in new_items:
            await self.send_item_to_channel(item)

    @stream.before_loop
    async def before_stream(self):
        await self.bot.wait_until_ready()

        self.subreddit = await self.reddit.subreddit("mod")
        self.channel = self.bot.get_channel(int(os.environ["pt_queue_channel"]))

        await self.channel.purge()
        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="reddit."
            )
        )

    @stream.after_loop
    async def after_stream(self):
        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="nothing. I'm broken."
            )
        )
        if not self.stream.is_being_cancelled():
            await self.wait_and_restart()

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

    async def create_embed(self, item):
        await item.author.load()
        timestamp = datetime.datetime.fromtimestamp(item.created_utc).isoformat()

        embed = {
            "color": 0xDA655F,
            "timestamp": timestamp,
            "footer": {"text": item.id},
            "fields": [],
        }

        if isinstance(item, comment.Comment):
            embed["fields"] += [
                {
                    "name": "Comment",
                    "value": f"**[{item.body[:900]}](https://www.reddit.com/{item.permalink})**",
                },
                {
                    "name": "Author (Karma)",
                    "value": f"**[{item.author}](https://www.reddit.com/u/{item.author})**"
                    + f" ({item.author.comment_karma})",
                },
            ]
            if item.parent_id.startswith("t1_"):
                parent_comment = await self.reddit.comment(item.parent_id)
                await parent_comment.author.load()

                embed["fields"].append(
                    {
                        "name": "In Reply To",
                        "value": f"[{parent_comment.body}](https://www.reddit.com/{parent_comment.permalink})",
                    }
                )
                embed["fields"].append(
                    {
                        "name": "Parent Comment Author",
                        "value": f"[{parent_comment.author}](https://www.reddit.com/u/{parent_comment.author})"
                        + f" ({parent_comment.author.comment_karma})",
                    }
                )

        if isinstance(item, submission.Submission):
            embed["fields"] += [
                {
                    "name": "Submission",
                    "value": f"**[{item.title}](https://www.reddit.com/u/{item.permalink})**",
                },
                {
                    "name": "Author (Karma)",
                    "value": f"**[{item.author}](https://www.reddit.com/u/{item.author})**"
                    + f" ({item.author.link_karma})",
                },
            ]

            if item.selftext:
                selftext = (
                    f"[{item.selftext[:900]}](https://www.reddit.com/{item.permalink})"
                )
                embed["fields"].append({"name": "Selftext", "value": selftext})

            if item.url.endswith((".jpg", ".jpeg", ".gif", ".gifv", ".png", ".svg")):
                image_url = item.url
                embed["image"] = {"url": item.url}
            elif "imgur.com" in item.url:
                image_url = item.url + ".jpg"
                embed["image"] = {"url": image_url}
            elif hasattr(item, "media_metadata"):
                try:
                    image_url = list(item.media_metadata.values())[0]["s"]["u"]
                    embed["image"] = {"url": image_url}
                except KeyError:
                    pass

        if item.user_reports or item.mod_reports:
            embed["color"] = 0xDFA936
            if item.mod_reports:
                report = item.user_reports[0][0]
                embed["fields"].append({"name": "User Reports", "value": report})
            if item.mod_reports:
                mod_report = item.mod_reports[0][0]
                embed["fields"].append({"name": "Mod Reports", "value": mod_report})

        return discord.Embed.from_dict(embed)

    async def create_view(self, item):
        view = View(item)
        await view.add_buttons()

        return view

    async def get_new_items(self):
        queue = await self.get_queue_items()
        channel = await self.get_channel_items()

        if channel.keys() == queue.keys():
            return {}

        for item_id in channel:
            if item_id in queue:
                del queue[item_id]
            else:
                try:
                    await channel[item_id].delete()
                except NotFound:
                    pass

        return reversed(list(queue.values()))

    async def get_queue_items(self):
        queue_items = {}
        try:
            async for item in self.subreddit.mod.modqueue():
                queue_items[item.id] = item
        except Exception as e:
            await self.wait_and_restart(e)

        return queue_items

    async def get_channel_items(self):
        channel_items = {}
        try:
            async for message in self.channel.history():
                if message.author == self.bot.user:
                    channel_items[message.embeds[0].footer.text] = message
        except Exception as e:
            await self.wait_and_restart(e)

        return channel_items

    async def send_item_to_channel(self, item):
        embed = await self.create_embed(item)
        view = await View.create(item)
        await self.channel.send(embed=embed, view=view)
