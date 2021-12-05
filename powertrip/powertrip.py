import datetime
import os
from asyncio import sleep

import discord
from asyncpraw import Reddit
from asyncpraw.models.reddit import comment, submission
from discord.errors import NotFound
from discord.ext import commands, tasks
from .view import View


class PowerTrip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel = None
        self.reddit = Reddit()
        self.subreddit = None
        self.stream.start()

    @tasks.loop(seconds=60)
    async def stream(self):
        new_items = await self.get_new_items()

        for item in new_items:
            await self.send_item_to_channel(new_items[item])

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

    def create_embed(self, item):
        color = 0xDA655F
        reports_color = 0xDFA936
        permalink = item.permalink
        item_url = f"https://www.reddit.com{permalink}"
        timestamp = datetime.datetime.fromtimestamp(item.created_utc).isoformat()
        author_name = item.author.name
        author_url = f"https://www.reddit.com/u/{item.author.name}"
        footer_text = f"{item.id}"

        embed = {
            "color": color,
            "url": item_url,
            "timestamp": timestamp,
            "author": {
                "name": author_name,
                "url": author_url,
            },
            "footer": {"text": footer_text},
        }
        if item.user_reports:
            report = item.user_reports[0][0]

            embed["color"] = reports_color
            embed["fields"] = [{"name": "Reports", "value": report}]

        if isinstance(item, comment.Comment):
            linked_comment = f"[{item.body}]({item_url})"

            embed["description"] = linked_comment

        if isinstance(item, submission.Submission):
            title = item.title[:256]
            embed["title"] = title

            if item.selftext:
                selftext = item.selftext[:4096]
                embed["description"] = selftext

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

        return dict(reversed(list(queue.items())))

    async def get_queue_items(self):
        queue_items = {}
        try:
            async for item in self.subreddit.mod.modqueue():
                queue_items[item.id] = item
        except Exception as e:
            await self.channel.purge()
            await self.channel.send(
                f"An error has occured getting the reddit modqueue:\n\n{e}\n\nTrying again in 5 minutes."
            )
            await sleep(300)
            await self.stream.restart()

        return queue_items

    async def get_channel_items(self):
        channel_items = {}
        try:
            async for message in self.channel.history():
                if message.author == self.bot.user:
                    channel_items[message.embeds[0].footer.text] = message
        except Exception as e:
            await self.channel.purge()
            await self.channel.send(
                f"An error has occured getting the discord channel history:\n\n{e}\n\nTrying again in 5 minutes."
            )
            await sleep(300)
            await self.stream.restart()

        return channel_items

    async def send_item_to_channel(self, item):
        embed = self.create_embed(item)
        view = await self.create_view(item)
        await self.channel.send(embed=embed, view=view)
