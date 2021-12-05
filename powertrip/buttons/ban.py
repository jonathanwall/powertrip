from .base import BaseButton
from discord.enums import ButtonStyle


class BanButton(BaseButton):
    def __init__(self, item, duration=None):
        if duration is None:
            label = f"Permanent Ban"
            style = ButtonStyle.red
        else:
            label = f"{duration} Day Ban"
            style = ButtonStyle.blurple

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
