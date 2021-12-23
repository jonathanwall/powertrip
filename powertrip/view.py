import os

from asyncpraw.models.reddit import comment, submission
from discord.ui import View

from powertrip import buttons


class View(View):
    def __init__(self, item, timeout=None):
        super().__init__(timeout=timeout)
        self.item = item

    def add_approve_button(self):
        self.add_item(buttons.Approve(self.item))

    def add_remove_button(self):
        self.add_item(buttons.Remove(self.item))

    def add_ban_button(self, duration):
        self.add_item(buttons.Ban(self.item, duration))

    def add_reason_button(self, reason):
        self.add_item(buttons.Reason(self.item, reason))

    async def add_buttons(self):
        self.add_approve_button()
        self.add_remove_button()
        if isinstance(self.item, submission.Submission):
            await self.add_reason_buttons()
        if isinstance(self.item, comment.Comment):
            self.add_ban_buttons()

    async def add_reason_buttons(self):
        async for reason in self.item.subreddit.mod.removal_reasons:
            self.add_reason_button(reason)

    def add_ban_buttons(self):
        durations = (
            os.environ["pt_ban_durations"].split(",")
            if "pt_ban_durations" in os.environ
            else [3, 7, 28]
        )
        durations += [None]
        for duration in durations:
            self.add_ban_button(duration)
