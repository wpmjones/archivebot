from discord.ext import commands
from config import settings, emojis, color_pick


class General(commands.Cog):
    """Default Archive commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="archive")
    async def archive(self, ctx, channel: str = "x"):
        if channel == "x":
            channel = ctx.channel
        await ctx.send(f"I'ma gonna create an archive named {channel}.")


def setup(bot):
    bot.add_cog(General(bot))