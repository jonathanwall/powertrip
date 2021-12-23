from .button import Button
from discord.enums import ButtonStyle


class ApproveButton(Button):
    def __init__(self, item):
        style = ButtonStyle.green
        label = "Approve"

        super().__init__(style=style, label=label)
        self.item = item

    async def callback(self, interaction):
        try:
            await self.item.mod.unlock()
            await self.item.mod.approve()
        except Exception as e:
            await self.handle_exception(interaction.message, e)
        else:
            await self.delete_message(interaction.message)
