import discord
from discord.ext import commands


class NewHelp(commands.Cog):
    """Replacement help file because I like really sexy help files"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", hidden=True)
    async def help(self, ctx, command: str = "all"):
        desc = ("All commands must begin with a slash.\n\n"
                "You can type /help <command> to display only the help for that command.")
        if command not in ["all", "archive", "search"]:
            self.bot.logger.error(f"Problem: /help {command} does not exist.")
            await ctx.send(f":x: You have provided a command that doesn't exist. Perhaps try "
                           f"`/help` to see all commands.")
            return
        embed = discord.Embed(title="Archive Bot by TubaKid", description=desc, color=discord.Color.green())
        embed.add_field(name="Commands:", value="-----------", inline=False)
        if command in ["all", "archive"]:
            help_text = ("Archives the channel you are in using the name of the channel (see option), "
                         "provides a link to the archive doc, then waits 10 minutes before deleting "
                         "the channel. Optional: you can include a document name after /archive if you "
                         "want to specify a name.")
            embed.add_field(name="/archive <document name>", value=help_text, inline=False)
        if command in ["all", "search"]:
            help_text = ("Searches existing Google Docs for the text specified.  It will search both "
                         "the title and body of the document, but the search is limited to archived "
                         "channels housed in the RCS Council Google Drive account.\nYou may want to "
                         "search by clan name or tag, but feel free to search for any text at all.\n\n"
                         "These are confidential documents.  Please do not share them outside of the "
                         "Scouting team.")
            embed.add_field(name="/search <search string>", value=help_text, inline=False)
        if command in ["all", "list"]:
            help_text = ("Responds with a link to the Google Drive folder containing all of the archived "
                         "documents.  These are confidential documents.  Please do not share them outside of the "
                         "Scouting team.")
            embed.add_field(name="/list", value=help_text, inline=False)
        embed.set_footer(icon_url="https://openclipart.org/image/300px/svg_to_png/122449/1298569779.png",
                         text="Archive Bot proudly maintained by TubaKid.")
        self.bot.logger.info(f"{ctx.command} by {ctx.author} in {ctx.channel} | "
                             f"Request complete: /help {command}")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(NewHelp(bot))