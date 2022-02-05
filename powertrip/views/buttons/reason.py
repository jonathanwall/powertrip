from .button import Button
from discord.enums import ButtonStyle


class Reason(Button):
    def __init__(self, item, reason):
        style = ButtonStyle.blurple
        label = reason.title

        super().__init__(style=style, label=label)
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
            await self.post.mod.send_removal_message(
                message, title=title, type=removal_type
            )
        except Exception as e:
            await self.handle_exception(interaction.message, e)
        else:
            await self.delete_message(interaction.message)
