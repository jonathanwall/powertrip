import datetime
import os
from asyncio import sleep

import discord
import uvloop
from asyncpraw import Reddit
from asyncpraw.models.reddit import comment, submission
from discord.errors import NotFound
from discord.ext import commands, tasks


class PowerTrip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel = None
        self.reddit = Reddit()
        self.subreddit = None
        self.stream.start()

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
        view = ItemView(item)
        await view.add_buttons()

        return view

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

    async def send_item_to_channel(self, item):
        embed = self.create_embed(item)
        view = await self.create_view(item)
        await self.channel.send(embed=embed, view=view)

    @tasks.loop()
    async def stream(self):
        queue_items = await self.get_new_items()

        for item in queue_items:
            await self.send_item_to_channel(queue_items[item])

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
            self.stream.restart()


class ErrorView(discord.ui.View):
    def __init__(self, error, timeout=None):
        super().__init__(timeout=timeout)
        self.error = error
        self.add_error_button()

    def add_error_button(self):
        self.add_item(self.ErrorButton(self.error))

    class ErrorButton(discord.ui.Button):
        def __init__(self, error):
            super().__init__(
                label=f"Error: {error}", disabled=True, style=discord.enums.ButtonStyle.gray
            )


class ItemView(discord.ui.View):
    def __init__(self, item, timeout=None):
        super().__init__(timeout=timeout)
        self.item = item

    def add_approve_button(self):
        self.add_item(ApproveButton(self.item))

    def add_remove_button(self):
        self.add_item(RemoveButton(self.item))

    def add_ban_button(self, duration):
        self.add_item(BanButton(self.item, duration))

    def add_reason_button(self, reason):
        self.add_item(ReasonButton(self.item, reason))

    async def add_buttons(self):
        self.add_approve_button()
        self.add_remove_button()
        if isinstance(self.item, submission.Submission):
            await self.add_reason_buttons()
        if isinstance(self.item, comment.Comment):
            self.add_ban_buttons()

    async def add_reason_buttons(self):
        async for reason in self.item.subreddit.mod.removal_reasons:
            self.add_reason_button(reason)

    def add_ban_buttons(self):
        durations = (
            os.environ["pt_ban_durations"].split(",")
            if "pt_ban_durations" in os.environ
            else [3, 7, 28]
        )
        durations += [None]
        for duration in durations:
            self.add_ban_button(duration)


class Button(discord.ui.Button):
    async def handle_exception(self, message, exception):
        view = ErrorView(exception)
        await message.edit(view=view)

    async def delete_message(self, message):
        try:
            await message.delete()
        except NotFound:
            pass


class ApproveButton(Button):
    def __init__(self, item):
        label = "Approve"
        style = discord.enums.ButtonStyle.green

        super().__init__(label=label, style=style)
        self.item = item

    async def callback(self, interaction):
        try:
            await self.item.mod.approve()
        except Exception as e:
            await self.handle_exception(interaction.message, e)
        else:
            await self.delete_message(interaction.message)


class RemoveButton(Button):
    def __init__(self, item):
        label = "Remove"
        style = discord.enums.ButtonStyle.grey

        super().__init__(label=label, style=style)
        self.item = item

    async def callback(self, interaction):
        try:
            await self.item.mod.remove()
        except Exception as e:
            await self.handle_exception(interaction.message, e)
        else:
            await self.delete_message(interaction.message)


class BanButton(Button):
    def __init__(self, item, duration=None):
        if duration is None:
            label = f"Permanent Ban"
            style = discord.enums.ButtonStyle.red
        else:
            label = f"{duration} Day Ban"
            style = discord.enums.ButtonStyle.blurple

        super().__init__(label=label, style=style)
        self.item = item
        self.duration = duration

    async def callback(self, interaction):
        ban_context = self.item.fullname
        ban_message = f"[{self.item.body}](https://www.reddit.com/{self.item.permalink})"
        ban_note = f"{interaction.user} from PowerTrip"
        ban_reason = f"this is the ban reason"

        ban_options = {
            "ban_context": ban_context,
            "ban_message": ban_message,
            "ban_reason": ban_reason,
            "note": ban_note,
        }
        if self.duration:
            ban_options["duration"] = self.duration

        try:
            await self.item.mod.remove()
            await self.item.subreddit.banned.add(self.item.author.name, **ban_options)
        except Exception as e:
            await self.handle_exception(interaction.message, e)
        else:
            await self.delete_message(interaction.message)


class ReasonButton(Button):
    def __init__(self, item, reason):
        label = reason.title
        style = discord.enums.ButtonStyle.blurple

        super().__init__(label=label, style=style)
        self.post = item
        self.reason = reason

    async def callback(self, interaction):
        mod_note = f"{interaction.user} via PowerTrip"
        reason_id = self.reason.id
        message = self.reason.message
        title = self.reason.title
        removal_type = "private"

        try:
            await self.post.mod.remove(mod_note=mod_note, reason_id=reason_id)
            await self.post.mod.send_removal_message(message, title=title, type=removal_type)
        except Exception as e:
            await self.handle_exception(interaction.message, e)
        else:
            await self.delete_message(interaction.message)


def main():
    bot = commands.Bot(description="PowerTrip: discord + reddit moderation helper")
    bot.add_cog(PowerTrip(bot))
    uvloop.install()
    bot.run(os.environ["pt_token"])


if __name__ == "__main__":
    main()
