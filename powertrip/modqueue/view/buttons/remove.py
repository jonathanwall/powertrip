from .button import Button
from discord.enums import ButtonStyle


class Remove(Button):
    def __init__(self):
        style = ButtonStyle.grey
        label = "Remove"

        super().__init__(style=style, label=label)

    async def callback(self, interaction):
        try:
            await self.view.item.mod.remove()
        except Exception as e:
            await self.handle_exception(interaction.message, e)
        else:
            await self.delete_message(interaction.message)
