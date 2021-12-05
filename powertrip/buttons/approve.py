from .base import BaseButton
from discord.enums import ButtonStyle


class ApproveButton(BaseButton):
    def __init__(self, item):
        label = "Approve"
        style = ButtonStyle.green

        super().__init__(label=label, style=style)
        self.item = item

    async def callback(self, interaction):
        try:
            await self.item.mod.approve()
        except Exception as e:
            await self.handle_exception(interaction.message, e)
        else:
            await self.delete_message(interaction.message)
