import datetime
import os
from asyncio import sleep

import discord
from asyncpraw import Reddit
from asyncpraw.models.reddit import comment, submission
from discord.ext import commands, tasks


class Approve(discord.ui.Button):
    def __init__(self):
        style = discord.ButtonStyle.green
        label = "Approve"

        super().__init__(style=style, label=label)

    async def callback(self, interaction):
        try:
            await self.view.item.mod.unlock()
            await self.view.item.mod.approve()
        except Exception as e:
            await self.handle_exception(interaction.message, e)
        else:
            await self.delete_message(interaction.message)


class Button(discord.ui.Button):
    async def delete_message(self, message):
        await sleep(0.5)
        try:
            await message.delete()
        except discord.NotFound:
            pass

    async def handle_exception(self, message, exception):
        view = Button.ExceptionView(exception)
        await message.edit(view=view)

    class ExceptionView(discord.ui.View):
        def __init__(self, exception, timeout=None):
            super().__init__(timeout=timeout)
            self.add_item(self.ExceptionButton(exception))

        class ExceptionButton(discord.ui.Button):
            def __init__(self, exception):
                super().__init__(
                    label=f"Error: {exception}"[:80],
                    disabled=True,
                    style=discord.enums.ButtonStyle.gray,
                )


class View(discord.ui.View):
    def __init__(self, item, timeout=None):
        super().__init__(timeout=timeout)
        self.item = item


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


async def create_view(item):
    view = View(item)
    view.add_item(Approve())
    return view


class ModQueueStream(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stream.start()

    @tasks.loop(seconds=5)
    async def stream(self):
        discord_queue = {}
        channel = self.bot.get_channel(int(os.environ["pt_queue_channel"]))
        async for message in channel.history():
            if message.author == self.bot.user:
                discord_queue[message.embeds[0].footer.text] = message
            else:
                try:
                    await message.delete()
                except (discord.Forbidden, discord.NotFound):
                    pass

        reddit_queue = {}
        try:
            subreddit = await self.bot.reddit.subreddit("mod")
        except Exception as e:
            pass
        try:
            async for item in subreddit.mod.modqueue():
                reddit_queue[item.id] = item
        except Exception as e:
            await self.wait_and_restart(e)

        if discord_queue.keys() == reddit_queue.keys():
            return

        for item_id in discord_queue:
            if item_id in reddit_queue:
                del reddit_queue[item_id]
            else:
                try:
                    await discord_queue[item_id].delete()
                except discord.NotFound:
                    pass

        for item in reversed(list(reddit_queue.values())):
            embed = await create_embed(item)
            view = await create_view(item)
            await channel.send(embed=embed, view=view)

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
            await self.wait_and_restart()

    async def wait_and_restart(self, error=None):
        channel = self.bot.get_channel(int(os.environ["pt_queue_channel"]))
        await channel.purge()
        if error is not None:
            message = f"The stream has encountered an error:\n`{error}`\nTrying again in 5 minutes."
        else:
            message = (
                f"The stream has encountered an error.\nTrying again in 5 minutes."
            )
        await channel.send(message)
        await sleep(300)
        self.stream.restart()


class Powertrip(discord.Bot):
    def __init__(self):
        discord.Bot.__init__(self)
        self.reddit = Reddit()
        self.add_cog(ModQueueStream(self))

    def run(self, token=None):
        if token is None:
            token = os.environ["pt_token"]
        super().run(token)


def main():
    pt = Powertrip()
    pt.run()


if __name__ == "__main__":
    main()
