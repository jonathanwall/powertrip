from .button import Button
from discord.enums import ButtonStyle


class Ban(Button):
    def __init__(self, duration=None):
        if duration is None:
            style = ButtonStyle.red
            label = f"Permanent Ban"
        else:
            style = ButtonStyle.blurple
            label = f"{duration} Day Ban"

        super().__init__(style=style, label=label)
        self.duration = duration

    async def callback(self, interaction):
        ban_context = self.view.item.fullname
        ban_message = f"[{self.view.item.body}](https://www.reddit.com/{self.view.item.permalink})"
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
            await self.view.item.mod.remove()
            await self.view.item.subreddit.banned.add(
                self.view.item.author.name, **ban_options
            )
        except Exception as e:
            await self.handle_exception(interaction.message, e)
        else:
            await self.delete_message(interaction.message)
