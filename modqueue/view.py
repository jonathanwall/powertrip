import discord
import asyncpraw
import os


class View(discord.ui.View):
    def __init__(self, item, timeout=None):
        super().__init__(timeout=timeout)
        self.item = item
        self.reason = None
        self.ban = None

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.blurple, row=4)
    async def approve(self, button, interaction):
        await self.item.approve()

        await interaction.message.delete(delay=0.25)

    @discord.ui.button(label="Remove", style=discord.ButtonStyle.red, row=4)
    async def remove(self, button, interaction):
        self.remove_item(button)
        self.final_remove_button()
        await self.reason_select()
        await self.ban_select()

        await interaction.message.edit(view=self)

    def final_remove_button(self):
        class FinalRemoveButton(discord.ui.Button):
            def __init__(self):
                super().__init__(label="Remove", style=discord.ButtonStyle.red, row=4)

            async def callback(self, interaction):
                mod_note = f"{interaction.user.display_name} via PowerTrip"

                if self.view.reason is not None:
                    await self.view.item.mod.remove(
                        mod_note=mod_note, reason_id=self.view.reason.id
                    )
                    await self.view.mod.send_removal_message(
                        self.view.reason.message,
                        title=self.view.reason.title,
                        type="private",
                    )
                else:
                    await self.view.item.mod.remove(mod_note=mod_note)

                if self.view.ban is not None:
                    # banning is poorly documented on praw and reddit api docs
                    ban_options = {}

                    if self.view.reason is not None:
                        # string no longer than 100 characters, not sent to the user
                        ban_options["ban_reason"] = self.view.reason.title[:100]

                    # if no duration is set, the ban will be permanent
                    if self.view.ban != "Perm":
                        if self.view.ban >= 1 and self.view.ban <= 999:
                            ban_options["duration"] = int(self.view.ban)

                    # raw markodown text, sent to the user
                    ban_options["ban_message"] = ""

                    # fullname of a thing
                    ban_options["ban_context"] = self.view.item.fullname

                    # a string no longer than 300 characters, not sent to the user
                    ban_options["note"] = mod_note[:300]

                    await self.view.item.subreddit.banned.add(
                        self.view.item.author, **ban_options
                    )

                await interaction.message.delete(delay=0.25)

        self.add_item(FinalRemoveButton())

    async def reason_select(self):
        class ReasonSelect(discord.ui.Select):
            def __init__(self, options):
                super().__init__(min_values=1, max_values=1, options=options, row=0)

            async def callback(self, interaction):
                try:
                    reason_id = self.values[0]
                    subreddit = self.view.item.subreddit
                    reason = await subreddit.mod.removal_reasons.get_reason(
                        reason_id=reason_id
                    )
                except asyncpraw.exceptions.ClientException:
                    reason = None
                self.view.reason = reason

        options = []
        options.append(
            discord.SelectOption(label="No Reason", value="None", default=True)
        )
        async for reason in self.item.subreddit.mod.removal_reasons:
            options.append(discord.SelectOption(label=reason.title, value=reason.id))
        reason_select = ReasonSelect(options=options)
        self.add_item(reason_select)

    async def ban_select(self):
        class BanSelect(discord.ui.Select):
            def __init__(self, options):
                super().__init__(min_values=1, max_values=1, options=options, row=1)

            async def callback(self, interaction):
                duration = self.values[0]
                if duration == "None":
                    self.view.ban = None
                else:
                    self.view.ban = duration

        durations = (
            os.environ["pt_ban_durations"].split(",")
            if "pt_ban_durations" in os.environ
            else [3, 7, 28]
        )
        options = [discord.SelectOption(label="Don't Ban", value="None", default=True)]
        for duration in durations:
            options.append(
                discord.SelectOption(label=f"{duration} Day Ban", value=duration)
            )
        options.append(discord.SelectOption(label="Permanent Ban", value="Perm"))

        ban_select = BanSelect(options=options)
        self.add_item(ban_select)
