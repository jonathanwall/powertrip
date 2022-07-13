import logging
import operator
import os

import discord
from asyncpraw.models.reddit.comment import Comment
from asyncpraw.models.reddit.submission import Submission
from discord import ButtonStyle, Interaction
from discord.ui import Item

log = logging.getLogger(__name__)


class View(discord.ui.View):
    def __init__(self, item, timeout: float = None):
        super().__init__(timeout=timeout)
        self.item = item
        self.reason = None
        self.ban = None
        self.add_item(ApproveButton())
        self.add_item(RemoveButton())

    async def log_interaction(self, interaction: Interaction) -> None:
        try:
            channel = interaction.guild.get_channel(int(os.environ["pt_log_channel"]))
        except AttributeError:
            return

        embed = interaction.message.embeds[0]
        if self.reason == "Approved":
            embed.color = discord.Color.green()
        else:
            embed.add_field(
                name="Reason",
                value=f"{self.reason.title if self.reason is not None else 'No Reason'}",
                inline=False,
            )
        if self.ban is not None:
            embed.add_field(name="Ban", value=f"{self.ban}", inline=False)
        embed.add_field(name="Mod", value=f"{interaction.user.display_name}", inline=False)
        await channel.send(embed=interaction.message.embeds[0])

    # Called when an item’s callback or interaction_check() fails with an error.
    async def on_error(self, error: Exception, item: Item, interaction: Interaction) -> None:
        log.error(f"{error.__module__}.{error.__class__.__name__}: {error}")
        await interaction.message.delete(delay=0)


class ApproveButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Approve", style=ButtonStyle.blurple, row=4)

    async def callback(self, interaction: Interaction) -> None:
        await self.view.item.mod.approve()
        self.view.reason = "Approved"
        await interaction.message.delete(delay=0)
        await self.view.log_interaction(interaction)


class RemoveButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Remove", style=ButtonStyle.red, row=4)

    async def callback(self, interaction: Interaction) -> None:
        self.view.clear_items()
        self.view.add_item(FinalRemoveButton())
        self.view.add_item(CancelButton())

        reasons = []
        reasons.append(discord.SelectOption(label="No Reason", value=".", default=True))
        async for reason in self.view.item.subreddit.mod.removal_reasons:
            reasons.append(discord.SelectOption(label=reason.title, value=reason.id))

        reasons.sort(key=operator.attrgetter("label"))

        self.view.add_item(ReasonSelect(options=reasons))

        durations = (
            os.environ["pt_ban_durations"].split(",")
            if "pt_ban_durations" in os.environ
            else [3, 7, 28]
        )
        bans = [discord.SelectOption(label="Don't Ban", value="None", default=True)]
        for duration in durations:
            option = discord.SelectOption(label=f"{duration} Day Ban", value=duration)
            bans.append(option)
        bans.append(discord.SelectOption(label="Permanent Ban", value="Perm"))
        self.view.add_item(BanSelect(options=bans))

        await interaction.message.edit(view=self.view)


class FinalRemoveButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Remove", style=ButtonStyle.red, row=4)

    async def callback(self, interaction: Interaction) -> None:
        log.debug("final_remove_callback")
        mod_note = f"{interaction.user.display_name} via PowerTrip"

        if self.view.reason is not None:
            await self.view.item.mod.remove(mod_note=mod_note, reason_id=self.view.reason.id)
            await self.view.item.mod.send_removal_message(
                self.view.reason.message,
                title=self.view.reason.title,
                type="private",
            )
        else:
            await self.view.item.mod.remove(mod_note=mod_note)

        if self.view.ban is not None:
            ban_options = {}
            ban_options["note"] = mod_note[:300]
            ban_options["ban_context"] = self.view.item.fullname

            # if no duration is set, the ban will be permanent
            if self.view.ban != "Perm":
                duration = int(self.view.ban)
                if duration >= 1 and duration <= 999:
                    ban_options["duration"] = duration

            ban_message = ""

            if isinstance(self.view.item, Comment):
                ban_message += (
                    "You have been banned for the following comment:"
                    + f"[{self.view.item.body}]"
                    + f"(https://www.reddit.com/{self.view.item.permalink})"
                )

            if isinstance(self.view.item, Submission):
                ban_message += (
                    "You have been banned for the following submission:"
                    + f"[{self.view.item.title}]"
                    + f"(https://www.reddit.com/{self.view.item.permalink})"
                )

            if self.view.reason is not None:
                ban_options["ban_reason"] = self.view.reason.title[:100]

                ban_message += (
                    f"\n\nThe moderator provided the following reason:"
                    + f" **{self.view.reason.title}**"
                )

            ban_options["ban_message"] = ban_message

            await self.view.item.subreddit.banned.add(self.view.item.author, **ban_options)

        await interaction.message.delete(delay=0)
        await self.view.log_interaction(interaction)


class ReasonSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(min_values=1, max_values=1, options=options, row=0)

    async def callback(self, interaction: Interaction) -> None:
        log.debug("reason_callback")
        try:
            reason_id = self.values[0]
            subreddit = self.view.item.subreddit
            reason = await subreddit.mod.removal_reasons.get_reason(reason_id=reason_id)
        except:
            reason = None
        self.view.reason = reason


class BanSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(min_values=1, max_values=1, options=options, row=1)

    async def callback(self, interaction: Interaction) -> None:
        log.debug("ban_callback")
        duration = self.values[0]
        if duration == "None":
            self.view.ban = None
        else:
            self.view.ban = duration


class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Cancel", style=ButtonStyle.gray, row=4)

    async def callback(self, interaction: Interaction) -> None:
        log.debug("cancel_callback")
        view = View(item=self.view.item)
        await interaction.message.edit(view=view)
