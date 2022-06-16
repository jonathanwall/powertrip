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

    async def interaction_check(self, interaction: Interaction) -> bool:
        log.debug("interaction_check")
        return await super().interaction_check(interaction)

    async def on_error(self, error: Exception, item: Item, interaction: Interaction) -> None:
        log.error("on_error")
        return await super().on_error(error, item, interaction)

    async def on_timeout(self):
        log.debug("on_timeout")
        return await super().on_timeout()


class ApproveButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Approve", style=ButtonStyle.blurple, row=4)

    async def callback(self, interaction: Interaction) -> None:
        log.debug("approve_callback")
        await self.view.item.mod.approve()
        await interaction.message.delete(delay=0)


class RemoveButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Remove", style=ButtonStyle.red, row=4)

    async def callback(self, interaction: Interaction) -> None:
        log.debug("remove_callback")
        self.view.clear_items()
        self.view.add_item(FinalRemoveButton())
        self.view.add_item(CancelButton())

        reasons = []
        reasons.append(discord.SelectOption(label="No Reason", value=".", default=True))
        async for reason in self.view.item.subreddit.mod.removal_reasons:
            reasons.append(discord.SelectOption(label=reason.title, value=reason.id))

        reasons.sort(key=operator.attrgetter("value"), reverse=True)

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
                    + f"\n[{self.view.item.body}]"
                    + f"(https://www.reddit.com/{self.view.item.permalink})"
                )

            if isinstance(self.view.item, Submission):
                ban_message += (
                    "You have been banned for the following submission:"
                    + f"\n[{self.view.item.title}]"
                    + f"(https://www.reddit.com/{self.view.item.permalink})"
                )

            if self.view.reason is not None:
                ban_options["ban_reason"] = self.view.reason.title[:100]

                ban_message += (
                    f"\nThe moderator provided the following reason:"
                    + f" **{self.view.reason.title}**"
                )

            ban_options["ban_message"] = ban_message

            await self.view.item.subreddit.banned.add(self.view.item.author, **ban_options)

        await interaction.message.delete(delay=0)


class ReasonSelect(discord.ui.Select):
    def __init__(self, options: list[discord.SelectOption]):
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
    def __init__(self, options: list[discord.SelectOption]):
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
