import traceback
import os
import git
# import asyncio
from loguru import logger
from discord.ext import commands
from config import settings

enviro = "dev"

if enviro == "LIVE":
    token = settings['discord']['archiveToken']
    prefix = "/"
    log_level = "INFO"
    coc_names = "vps"
else:
    token = settings['discord']['testToken']
    prefix = "."
    log_level = "DEBUG"
    coc_names = "dev"

logger.add("archivebot.log", rotation="50MB", level=log_level)

description = """Discord Archive Bot - by TubaKid"""

bot = commands.Bot(command_prefix=prefix, description=description, case_insensitive=True)


@bot.event
async def on_ready():
    logger.info("-------")
    logger.info(f"Logged in as {bot.user}")
    logger.info("-------")
    bot.test_channel = bot.get_channel(settings['oakChannels']['testChat'])
    await bot.test_channel.send("Archive Bot is now active")


@bot.event
async def on_resumed():
    logger.info('resumed...')

initialExtensions = ["cogs.general",
                     "cogs.owner",
                     ]

if __name__ == "__main__":
    bot.remove_command("help")
    bot.repo = git.Repo(os.getcwd())
    # loop = asyncio.get_event_loop()
    # bot.loop = loop
    bot.logger = logger

    for extension in initialExtensions:
        try:
            bot.load_extension(extension)
            logger.debug(f"{extension} loaded successfully")
        except Exception as e:
            logger.info(f"Failed to load extension {extension}")
            traceback.print_exc()

    bot.run(token)
