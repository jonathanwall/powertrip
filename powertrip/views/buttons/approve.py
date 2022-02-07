from .button import Button
from discord.enums import ButtonStyle


class Approve(Button):
    def __init__(self):
        style = ButtonStyle.green
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
