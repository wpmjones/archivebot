import discord
import traceback
import os
import git
import asyncio

from discord.ext import commands
from cogs.utils.db import ArchiveDB
from datetime import datetime
from loguru import logger
from config import settings

enviro = "home"

if enviro == "LIVE":
    token = settings['discord']['archiveToken']
    prefix = "/"
    log_level = "INFO"
    coc_names = "vps"
elif enviro == "home":
    token = settings['discord']['testToken']
    prefix = ">"
    log_level = "DEBUG"
    coc_names = "ubuntu"
else:
    token = settings['discord']['testToken']
    prefix = ">"
    log_level = "DEBUG"
    coc_names = "dev"

initialExtensions = ["cogs.general",
                     "cogs.admin",
                     "cogs.newhelp",
                     ]

description = """Discord Archive Bot - by TubaKid"""


class ArchiveBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=prefix,
                         description=description,
                         case_insensitive=True)
        self.remove_command("help")
        self.logger = logger
        self.messages = {}

    @property
    def log_channel(self):
        return self.get_channel(settings['logChannels']['archive'])

    async def on_ready(self):
        logger.info("-------")
        logger.info(f"Logged in as {self.user}")
        logger.info("-------")

    async def on_message_delete(self, message):
        if message.id in self.messages:
            del_message = self.messages[message.id]
            await del_message.delete()
            del self.messages[message.id]

    def send_log(self, message):
        asyncio.ensure_future(self.send_message(message))

    async def send_message(self, message):
        if len(message) < 2000:
            await self.log_channel.send(f"`{message}`")
        else:
            await self.log_channel.send(f"`{message[:1950]}`")

    async def after_ready(self):
        await self.wait_until_ready()
        logger.add(self.send_log, level=log_level)

    async def on_error(self, event_method, *args, **kwargs):
        embed = discord.Embed(title="Discord Event Error", color=0xa32952)
        embed.add_field(name="Event", value=event_method)
        embed.description = f"```py\n{traceback.format_exc()}\n```"
        embed.timestamp = datetime.utcnow()
        args_str = ["```py"]
        for index, arg in enumerate(args):
            args_str.append(f"[{index}]: {args!r}")
        args_str.append("```")
        embed.add_field(name="Args", value="\n".join(args_str), inline=False)
        try:
            await self.log_channel.send(embed=embed)
        except:
            pass


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    bot = ArchiveBot()
    bot.repo = git.Repo(os.getcwd())
    bot.db = ArchiveDB(bot)
    bot.pool = loop.run_until_complete(bot.db.create_pool())
    bot.loop = loop

    for extension in initialExtensions:
        try:
            bot.load_extension(extension)
            logger.debug(f"{extension} loaded successfully")
        except Exception as e:
            logger.info(f"Failed to load extension {extension}")
            traceback.print_exc()

    bot.run(token)
