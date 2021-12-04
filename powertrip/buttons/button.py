from discord.ui import Button
from discord.errors import NotFound

from powertrip.views import ErrorView


class Button(Button):
    async def handle_exception(self, message, exception):
        view = ErrorView(exception)
        await message.edit(view=view)

    async def delete_message(self, message):
        try:
            await message.delete()
        except NotFound:
            pass