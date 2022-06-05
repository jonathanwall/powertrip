import datetime
import logging
import os

import discord
import asyncpraw
from asyncpraw.models.reddit import comment, submission
from discord.ext import commands, tasks

logging.basicConfig(level=logging.WARN)
log = logging.getLogger(__name__)


class View(discord.ui.View):
    def __init__(self, item, timeout=None):
        super().__init__(timeout=timeout)
        self.item = item
        self.reason = None
        self.ban = None

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.blurple, row=4)
    async def approve(self, button, interaction):
        await self.item.approve()

        await interaction.message.delete(delay=0.25)

    @discord.ui.button(label="Remove", style=discord.ButtonStyle.red, row=4)
    async def remove(self, button, interaction):
        self.remove_item(button)
        self.final_remove_button()
        await self.reason_select()
        await self.ban_select()

        await interaction.message.edit(view=self)

    def final_remove_button(self):
        class FinalRemoveButton(discord.ui.Button):
            def __init__(self):
                super().__init__(label="Remove", style=discord.ButtonStyle.red, row=4)

            async def callback(self, interaction):
                mod_note = f"{interaction.user.display_name} via PowerTrip"

                if self.view.reason is not None:
                    await self.view.item.mod.remove(
                        mod_note=mod_note, reason_id=self.view.reason.id
                    )
                    await self.view.mod.send_removal_message(
                        self.view.reason.message,
                        title=self.view.reason.title,
                        type="private",
                    )
                else:
                    await self.view.item.mod.remove(mod_note=mod_note)

                if self.view.ban is not None:
                    # banning is poorly documented on praw and reddit api
                    ban_options = {}

                    if self.view.reason is not None:
                        # string no longer than 100 characters, not sent to the user
                        ban_options["ban_reason"] = self.view.reason.title[:100]

                    # if no duration is set, the ban will be permanent
                    if self.view.ban != "Perm":
                        # integer between 1 and 999, length of ban in days
                        ban_options["duration"] = int(self.view.ban)

                    # raw markodown text, sent to the user
                    ban_options["ban_message"] = ""

                    # fullname of a thing
                    ban_options["ban_context"] = self.view.item.fullname

                    # a string no longer than 300 characters, not sent to the user
                    ban_options["note"] = mod_note[:300]

                    await self.view.item.subreddit.banned.add(
                        self.view.item.author, **ban_options
                    )

                await interaction.message.delete(delay=0.25)

        self.add_item(FinalRemoveButton())

    async def reason_select(self):
        class ReasonSelect(discord.ui.Select):
            def __init__(self, options):
                super().__init__(min_values=1, max_values=1, options=options, row=0)

            async def callback(self, interaction):
                try:
                    reason_id = self.values[0]
                    subreddit = self.view.item.subreddit
                    reason = await subreddit.mod.removal_reasons.get_reason(
                        reason_id=reason_id
                    )
                except asyncpraw.exceptions.ClientException:
                    reason = None
                self.view.reason = reason

        options = []
        options.append(
            discord.SelectOption(label="No Reason", value="None", default=True)
        )
        async for reason in self.item.subreddit.mod.removal_reasons:
            options.append(discord.SelectOption(label=reason.title, value=reason.id))
        reason_select = ReasonSelect(options=options)
        self.add_item(reason_select)

    async def ban_select(self):
        class BanSelect(discord.ui.Select):
            def __init__(self, options):
                super().__init__(min_values=1, max_values=1, options=options, row=1)

            async def callback(self, interaction):
                duration = self.values[0]
                if duration == "None":
                    self.view.ban = None
                else:
                    self.view.ban = duration

        durations = (
            os.environ["pt_ban_durations"].split(",")
            if "pt_ban_durations" in os.environ
            else [3, 7, 28]
        )
        options = [discord.SelectOption(label="Don't Ban", value="None", default=True)]
        for duration in durations:
            options.append(
                discord.SelectOption(label=f"{duration} Day Ban", value=int(duration))
            )
        options.append(discord.SelectOption(label="Permanent Ban", value="Perm"))

        ban_select = BanSelect(options=options)
        self.add_item(ban_select)


async def create_embed(item):
    try:
        await item.author.load()
    except:
        pass
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
                "value": f"**[{item.body[:900]}](https://www.reddit.com{item.permalink})**",
            }
        ]

        if hasattr(item.author, "comment_karma"):
            embed["fields"].append(
                {
                    "name": "Author",
                    "value": f"**[{item.author}](https://www.reddit.com/u/{item.author})**",
                }
            )

    if isinstance(item, submission.Submission):
        embed["fields"] += [
            {
                "name": "Submission",
                "value": f"**[{item.title}](https://www.reddit.com{item.permalink})**",
            },
            {
                "name": "Author",
                "value": f"**[{item.author}](https://www.reddit.com/u/{item.author})**",
            },
        ]

        if item.selftext:
            selftext = (
                f"[{item.selftext[:900]}](https://www.reddit.com{item.permalink})"
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
        if item.user_reports:
            report = item.user_reports[0][0]
            embed["fields"].append({"name": "User Reports", "value": report})
        if item.mod_reports:
            mod_report = item.mod_reports[0][0]
            embed["fields"].append({"name": "Mod Reports", "value": mod_report})

    return discord.Embed.from_dict(embed)


class ModQueueStream(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stream.start()

    @tasks.loop(seconds=5)
    async def stream(self):
        discord_queue = {}
        discord_queue_channel = self.bot.get_channel(
            int(os.environ["pt_queue_channel"])
        )

        async for message in discord_queue_channel.history():
            if message.author == self.bot.user:
                item_id = message.embeds[0].footer.text
                discord_queue[item_id] = message

        reddit_queue = {}
        subreddit = await self.bot.reddit.subreddit("mod")
        async for item in subreddit.mod.modqueue():
            reddit_queue[item.id] = item

        for item_id in discord_queue:
            if item_id in reddit_queue:
                del reddit_queue[item_id]
            else:
                await discord_queue[item_id].delete(delay=0)

        for item in reversed(list(reddit_queue.values())):
            embed = await create_embed(item)
            view = View(item)
            await discord_queue_channel.send(embed=embed, view=view)

    @stream.before_loop
    async def before_stream(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(int(os.environ["pt_queue_channel"]))
        await channel.purge()
        await self.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name="reddit."
            )
        )

    @stream.after_loop
    async def after_stream(self):
        if not self.stream.is_being_cancelled():
            self.stream.restart()


class Powertrip(discord.Bot):
    def __init__(self):
        discord.Bot.__init__(self)
        self.reddit = asyncpraw.Reddit()

    def run(self, token=None):
        if token is None:
            token = os.environ["pt_token"]
        self.add_cog(ModQueueStream(self))
        super().run(token)


def main():
    pt = Powertrip()
    pt.run()


if __name__ == "__main__":
    main()
