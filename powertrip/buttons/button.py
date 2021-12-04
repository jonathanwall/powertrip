from discord.ui import Button
from discord.errors import NotFound
from asyncio import sleep

from powertrip.views import ErrorView


class Button(Button):
    async def handle_exception(self, message, exception):
        view = ErrorView(exception)
        await message.edit(view=view)

    async def delete_message(self, message):
        await sleep(1)
        try:
            await message.delete()
        except NotFound:
            pass
