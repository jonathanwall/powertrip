from asyncio import sleep

from discord.enums import ButtonStyle
from discord.errors import NotFound
from discord.ui import Button, View


class Button(Button):
    async def delete_message(self, message):
        await sleep(0.5)
        try:
            await message.delete()
        except NotFound:
            pass

    async def handle_exception(self, message, exception):
        view = Button.ExceptionView(exception)
        await message.edit(view=view)

    class ExceptionView(View):
        def __init__(self, exception, timeout=None):
            super().__init__(timeout=timeout)
            self.add_item(self.ExceptionButton(exception))

        class ExceptionButton(Button):
            def __init__(self, exception):
                super().__init__(
                    label=f"Error: {exception}"[:80], disabled=True, style=ButtonStyle.gray
                )
