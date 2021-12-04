from .button import Button
from discord.enums import ButtonStyle


class RemoveButton(Button):
    def __init__(self, item):
        label = "Remove"
        style = ButtonStyle.grey

        super().__init__(label=label, style=style)
        self.item = item

    async def callback(self, interaction):
        try:
            await self.item.mod.remove()
        except Exception:
            await self.handle_exception(interaction.message, Exception)
        else:
            await self.delete_message(interaction.message)
