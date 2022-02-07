import discord
import datetime
from asyncpraw.models.reddit import comment, submission


async def create_embed(item):
    await item.author.load()
    timestamp = datetime.datetime.fromtimestamp(item.created_utc).isoformat()

    embed = {
        "color": 0xDA655F,
        "timestamp": timestamp,
        "footer": {"text": item.id},
        "fields": [],
    }

    if isinstance(item, comment.Comment):
        embed["fields"] += [
            {
                "name": "Comment",
                "value": f"**[{item.body[:900]}](https://www.reddit.com{item.permalink})**",
            }
        ]

        if hasattr(item.author, "comment_karma"):
            embed["fields"].append(
                {
                    "name": "Author (Karma)",
                    "value": f"**[{item.author}](https://www.reddit.com/u/{item.author})**"
                    + f" ({item.author.comment_karma})",
                }
            )
        if item.parent_id.startswith("t1_"):
            try:
                parent_comment = await self.bot.reddit.comment(item.parent_id)
                await parent_comment.author.load()

                embed["fields"].append(
                    {
                        "name": "In Reply To",
                        "value": f"[{parent_comment.body[:900]}](https://www.reddit.com{parent_comment.permalink})",
                    }
                )
                embed["fields"].append(
                    {
                        "name": "Parent Comment Author",
                        "value": f"[{parent_comment.author}](https://www.reddit.com/u/{parent_comment.author})"
                        + f" ({parent_comment.author.comment_karma})",
                    }
                )
            except:
                pass

    if isinstance(item, submission.Submission):
        embed["fields"] += [
            {
                "name": "Submission",
                "value": f"**[{item.title}](https://www.reddit.com{item.permalink})**",
            },
            {
                "name": "Author (Karma)",
                "value": f"**[{item.author}](https://www.reddit.com/u/{item.author})**"
                + f" ({item.author.link_karma})",
            },
        ]

        if item.selftext:
            selftext = (
                f"[{item.selftext[:900]}](https://www.reddit.com{item.permalink})"
            )
            embed["fields"].append({"name": "Selftext", "value": selftext})

        if item.url.endswith((".jpg", ".jpeg", ".gif", ".gifv", ".png", ".svg")):
            image_url = item.url
            embed["image"] = {"url": item.url}
        elif "imgur.com" in item.url:
            image_url = item.url + ".jpg"
            embed["image"] = {"url": image_url}
        elif hasattr(item, "media_metadata"):
            try:
                image_url = list(item.media_metadata.values())[0]["s"]["u"]
                embed["image"] = {"url": image_url}
            except KeyError:
                pass

    if item.user_reports or item.mod_reports:
        embed["color"] = 0xDFA936
        if item.user_reports:
            report = item.user_reports[0][0]
            embed["fields"].append({"name": "User Reports", "value": report})
        if item.mod_reports:
            mod_report = item.mod_reports[0][0]
            embed["fields"].append({"name": "Mod Reports", "value": mod_report})

    return discord.Embed.from_dict(embed)
