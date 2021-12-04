from discord.ui import Button, View
from discord.enums import ButtonStyle


class ErrorView(View):
    def __init__(self, error, timeout=None):
        super().__init__(timeout=timeout)
        self.error = error
        self.add_error_button()

    def add_error_button(self):
        self.add_item(self.ErrorButton(self.error))

    class ErrorButton(Button):
        def __init__(self, error):
            super().__init__(label=f"Error: {error}"[:80], disabled=True, style=ButtonStyle.gray)
