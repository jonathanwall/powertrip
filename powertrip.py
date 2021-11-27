import datetime
import os
from asyncio import sleep

import discord
import uvloop
from asyncpraw import Reddit
from asyncpraw.models.reddit import comment, submission
from discord.ext import commands, tasks


class PowerTrip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel = None
        self.reddit = Reddit()
        self.subreddit = None
        self.stream.start()

    @tasks.loop()
    async def stream(self):
        discord = {}
        async for message in self.channel.history():
            if message.author == self.bot.user:
                discord[message.embeds[0].footer.text] = message

        reddit = {}
        async for item in self.subreddit.mod.modqueue():
            reddit[item.id] = item

        if discord.keys() == reddit.keys():
            return

        for item_id in discord:
            if item_id not in reddit:
                try:
                    await discord[item_id].delete()
                except discord.errors.NotFound:
                    pass
            else:
                del reddit[item_id]

        for item in dict(reversed(list(reddit.items()))):
            await self.channel.send(embed=embed(reddit[item]), view=await view(reddit[item]))

    @stream.before_loop
    async def before_stream(self):
        await self.bot.wait_until_ready()

        self.subreddit = await self.reddit.subreddit("mod")
        self.channel = self.bot.get_channel(int(os.environ["pt_queue_channel"]))

        await self.channel.purge()
        await self.bot.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="reddit")
        )

    @stream.after_loop
    async def after_stream(self):
        if not self.stream.is_being_cancelled():
            await self.channel.purge()
            await self.channel.send("Stream error. Trying again in five minutes.")
            await sleep(300)
            self.stream.restart()


class ItemView(discord.ui.View):
    def __init__(self, item):
        super().__init__(timeout=None)
        self.item = item

    async def add_buttons(self):
        self.add_item(ApproveButton(self.item))
        self.add_item(RemoveButton(self.item))
        if isinstance(self.item, submission.Submission):
            await self.add_reason_buttons()
        if isinstance(self.item, comment.Comment):
            self.add_ban_buttons()

    async def add_reason_buttons(self):
        async for reason in self.item.subreddit.mod.removal_reasons:
            self.add_item(ReasonButton(self.item, reason))

    def add_ban_buttons(self):
        durations = (
            os.environ["pt_ban_durations"].split(",")
            if "pt_ban_durations" in os.environ
            else [3, 7, 28]
        )
        durations += [None]
        for duration in durations:
            self.add_item(BanButton(comment, duration))


class ApproveButton(discord.ui.Button):
    def __init__(self, item):
        super().__init__(label="Approve", style=discord.enums.ButtonStyle.green)
        self.item = item

    async def callback(self, interaction):
        await self.item.mod.approve()
        try:
            await interaction.message.delete()
        except discord.errors.NotFound:
            pass


class RemoveButton(discord.ui.Button):
    def __init__(self, item):
        super().__init__(label="Remove", style=discord.enums.ButtonStyle.grey)
        self.item = item

    async def callback(self, interaction):
        await self.item.mod.remove()
        try:
            await interaction.message.delete()
        except discord.errors.NotFound:
            pass


class BanButton(discord.ui.Button):
    def __init__(self, item, duration=None):
        if duration is None:
            label = f"🔨 perm ban"
        else:
            label = f"{duration} day ban"

        super().__init__(label=label, style=discord.enums.ButtonStyle.red)
        self.item = item
        self.duration = duration

    async def callback(self, interaction):
        await self.item.mod.remove()
        ban_options = {
            "ban_context": self.item.name,
            "ban_message": f"[{self.item.body}](https://www.reddit.com/{self.item.permalink})",
            "note": f"{interaction.user} from PowerTrip",
        }
        if self.duration:
            ban_options["duration"] = self.duration
        await self.item.subreddit.banned.add(self.item.author.name, **ban_options)
        try:
            await interaction.message.delete()
        except discord.errors.NotFound:
            pass


class ReasonButton(discord.ui.Button):
    def __init__(self, post, reason):
        super().__init__(label=reason.title, style=discord.enums.ButtonStyle.blurple)
        self.post = post
        self.reason = reason

    async def callback(self, interaction):
        await self.post.mod.remove(
            mod_note=f"{interaction.user} via PowerTrip", reason_id=self.reason.id
        )
        await self.post.mod.send_removal_message(
            self.reason.message, title=self.reason.title, type="private"
        )
        try:
            await interaction.message.delete()
        except discord.errors.NotFound:
            pass


def embed(item):
    embed = {
        "color": 0xDA655F,
        "url": f"https://www.reddit.com{item.permalink}",
        "timestamp": datetime.datetime.fromtimestamp(item.created_utc).isoformat(),
        "author": {
            "name": item.author.name,
            "url": f"https://www.reddit.com/u/{item.author.name}",
        },
        "footer": {"text": f"{item.id}"},
    }
    if item.user_reports:
        embed["color"] = 0xDFA936
        embed["fields"] = [{"name": "Reports", "value": item.user_reports[0][0]}]

    if isinstance(item, comment.Comment):
        embed["description"] = f"[{item.body}](https://www.reddit.com{item.permalink})"
    if isinstance(item, submission.Submission):
        embed["title"] = item.title[:256]
        if item.selftext:
            embed["description"] = item.selftext[:4096]

        if item.url.endswith((".jpg", ".jpeg", ".gif", ".gifv", ".png", ".svg")):
            embed["image"] = {"url": item.url}
        elif "imgur.com" in item.url:
            embed["image"] = {"url": item.url + ".jpg"}
        elif hasattr(item, "media_metadata"):
            try:
                embed["image"] = {"url": list(item.media_metadata.values())[0]["s"]["u"]}
            except KeyError:
                pass

    return discord.Embed.from_dict(embed)


async def view(item):
    view = ItemView(item)
    await view.add_buttons()
    return view


def main():
    bot = commands.Bot(description="PowerTrip: discord + reddit moderation helper")
    bot.add_cog(PowerTrip(bot))
    uvloop.install()
    bot.run(os.environ["pt_token"])


if __name__ == "__main__":
    main()
