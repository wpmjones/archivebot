import traceback
import os
import git
import asyncio
from cogs.utils.db import ArchiveDB
from loguru import logger
from discord.ext import commands
from config import settings

enviro = "LIVE"

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

description = """Discord Archive Bot - by TubaKid"""

bot = commands.Bot(command_prefix=prefix, description=description, case_insensitive=True)


@bot.event
async def on_ready():
    logger.info("-------")
    logger.info(f"Logged in as {bot.user}")
    logger.info("-------")


@bot.event
async def on_message_delete(message):
    if message.id in bot.messages:
        del_message = bot.messages[message.id]
        await del_message.delete()
        del bot.messages[message.id]

initialExtensions = ["cogs.general",
                     "cogs.admin",
                     "cogs.newhelp",
                     ]


def send_log(message):
    asyncio.ensure_future(send_message(message))


async def send_message(message):
    if len(message) < 2000:
        await bot.get_channel(settings['logChannels']['archive']).send(f"`{message}`")
    else:
        await bot.get_channel(settings['logChannels']['archive']).send(f"`{message[:1950]}`")

logger.add("archivebot.log", rotation="50MB", level=log_level)


async def after_ready():
    await bot.wait_until_ready()
    logger.add(send_log, level="DEBUG")

if __name__ == "__main__":
    bot.remove_command("help")
    bot.repo = git.Repo(os.getcwd())
    bot.db = ArchiveDB(bot)
    loop = asyncio.get_event_loop()
    bot.pool = loop.run_until_complete(bot.db.create_pool())
    loop.create_task(after_ready())
    bot.logger = logger
    # Set up for message deletion
    bot.messages = {}

    for extension in initialExtensions:
        try:
            bot.load_extension(extension)
            logger.debug(f"{extension} loaded successfully")
        except Exception as e:
            logger.info(f"Failed to load extension {extension}")
            traceback.print_exc()

    bot.run(token)
