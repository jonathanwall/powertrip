from .base import BaseButton
from discord.enums import ButtonStyle


class ApproveButton(BaseButton):
    def __init__(self, item, log_channel=None):
        style = ButtonStyle.green
        label = "Approve"

        super().__init__(style=style, label=label)
        self.item = item
        self.log_channel = log_channel

    async def callback(self, interaction):
        try:
            await self.item.mod.unlock()
            await self.item.mod.approve()
        except Exception as e:
            await self.handle_exception(interaction.message, e)
        else:
            await self.log_action()
            await self.delete_message(interaction.message)
