import os

import discord
from asyncpraw.models.reddit import comment, submission

from . import buttons


class View(discord.ui.View):
    def __init__(self, item, timeout=None):
        super().__init__(timeout=timeout)
        self.item = item

    # @classmethod
    # async def modqueue(cls, item, timeout=None):
    #     self = cls(item, timeout=timeout)
    #     self.add_item(buttons.Approve())
    #     self.add_item(buttons.Remove())
    #     if isinstance(self.item, submission.Submission):
    #         async for reason in self.item.subreddit.mod.removal_reasons:
    #             self.add_item(buttons.Reason(reason))
    #     if isinstance(self.item, comment.Comment):
    #         durations = (
    #             os.environ["pt_ban_durations"].split(",")
    #             if "pt_ban_durations" in os.environ
    #             else [3, 7, 28]
    #         )
    #         durations += [None]
    #         for duration in durations:
    #             self.add_item(buttons.Ban(duration))
    #     return self


async def create_view(item):
    view = View(item)
    view.add_item(buttons.Approve())
    view.add_item(buttons.Remove())
    if isinstance(view.item, submission.Submission):
        async for reason in view.item.subreddit.mod.removal_reasons:
            view.add_item(buttons.Reason(reason))
    if isinstance(view.item, comment.Comment):
        durations = (
            os.environ["pt_ban_durations"].split(",")
            if "pt_ban_durations" in os.environ
            else [3, 7, 28]
        )
        durations += [None]
        for duration in durations:
            view.add_item(buttons.Ban(duration))
    return view
