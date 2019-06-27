import pickle
import os.path
from discord.ext import commands
from config import settings
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Connect to Google Sheets
scope = "https://www.googleapis.com/auth/drive"
creds = None
if os.path.exists("token.pickle"):
    with open("token.pickle", "rb") as token:
        creds = pickle.load(token)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", scope)
        creds = flow.run_local_server()
    # Save the credentials for the next run
    with open("token.pickle", "wb") as token:
        pickle.dump(creds, token)
service = build("docs", "v1", credentials=creds)


class General(commands.Cog):
    """Default Archive commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="archive")
    async def archive(self, ctx, channel: str = "x"):
        if channel == "x":
            channel = ctx.channel
        await ctx.send(f"I'ma gonna create an archive named {channel}.")
        title = "ARCHIVE - " + channel
        body = {
            "title": title
        }
        doc = service.documents().create(body=body).execute()
        await ctx.send(f"Created document with title: {doc.get('title')}")


def setup(bot):
    bot.add_cog(General(bot))