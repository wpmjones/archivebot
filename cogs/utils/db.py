import asyncpg
from config import settings


class ArchiveDB:
    def __init__(self, bot):
        self.bot = bot

    async def create_pool(self):
        pool = await asyncpg.create_pool(settings['pg']['uri2'] + "/rcsdata", max_size=15)
        return pool