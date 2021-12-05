from asyncio import sleep

from discord.enums import ButtonStyle
from discord.errors import NotFound
from discord.ui import Button, View


class BaseButton(Button):
    async def handle_exception(self, message, exception):
        view = ExceptionView(exception)
        await message.edit(view=view)

    async def delete_message(self, message):
        await sleep(1)
        try:
            await message.delete()
        except NotFound:
            pass


class ExceptionView(View):
    def __init__(self, error, timeout=None):
        super().__init__(timeout=timeout)
        self.error = error
        self.add_error_button()

    def add_error_button(self):
        self.add_item(self.ErrorButton(self.error))

    class ErrorButton(Button):
        def __init__(self, error):
            super().__init__(label=f"Error: {error}"[:80], disabled=True, style=ButtonStyle.gray)
