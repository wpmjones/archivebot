import pickle
import os.path
import asyncio
from datetime import datetime
from discord.ext import commands
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
drive_service = build("drive", "v3", credentials=creds)


class General(commands.Cog):
    """Default Archive commands"""
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="search")
    async def search(self, ctx, search_str):
        results = drive_service.files().list(pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        file_list = ""
        for item in items:
            if search_str.lower() in item['name'].lower() and "ARCHIVE" in item['name']:
                file_list += f"{item['name']} <https://docs.google.com/document/d/{item['id']}/edit>\n"
        if file_list != "":
            content = "**Files found:**\n" + file_list
            await ctx.send(content)
        else:
            await ctx.send(f"No files found with the text {search_str} in the title.")

    @commands.command(name="archive")
    @commands.has_role("Council")
    async def archive(self, ctx, channel: str = "x"):
        if channel == "x":
            channel = ctx.channel.name
        now = datetime.utcnow().strftime("%d %B %Y, %H:%M:%S")
        len_now = (len(now.encode('utf-16-le')) / 2) + 4
        doc_name = f"ARCHIVE - {channel.replace('-',' ').title()}"
        len_doc_name = len(doc_name.encode('utf-16-le')) / 2
        await ctx.send(f"I'ma gonna create an archive named {doc_name}.")
        template_id = "15iTyuU5lax8dJiE1ur9MDnIMm3YCFnlfSXH3pSzJzhk"
        body = {"name": doc_name}
        new_doc = drive_service.files().copy(fileId=template_id, body=body).execute()
        doc_copy_id = new_doc.get('id')
        doc_copy_link = f"https://docs.google.com/document/d/{doc_copy_id}/edit"
        # Add perms for those with a link to view
        body = {
            "role": "reader",
            "type": "anyone"
        }
        response = drive_service.permissions().create(fileId=doc_copy_id, body=body).execute()
        # Modify template fields and add messages
        requests = [
            {
                "replaceAllText": {
                    "containsText": {
                        "text": "{{CHANNEL_NAME}}",
                        "matchCase": "true"
                    },
                    "replaceText": doc_name
                }
            }, {
                "replaceAllText": {
                    "containsText": {
                        "text": "{{DATE}}",
                        "matchCase": "true"
                    },
                    "replaceText": f"{now} GMT"
                }
            }
        ]
        # Get message from Discord here
        start = len_doc_name + len_now + 7
        async for message in ctx.channel.history(before=ctx.message, oldest_first=True):
            len_author = len(message.author.display_name.encode('utf-16-le')) / 2
            requests.append({
                "insertText": {
                    "location": {
                        "index": start
                    },
                    "text": message.author.display_name + "\n"
                }
            })
            requests.append({
                "updateTextStyle": {
                    "range": {
                        "startIndex": start,
                        "endIndex": start + len_author
                    },
                    "textStyle": {"bold": True},
                    "fields": "bold"
                }
            })
            start += len_author + 1
            created = message.created_at.strftime("%d %B %Y, %H:%M:%S")
            len_date = len(created.encode('utf-16-le')) / 2
            requests.append({
                "insertText": {
                    "location": {
                        "index": start
                    },
                    "text": created + "\n\n"
                }
            })
            start += len_date + 2
            len_message = len(message.content.encode('utf-16-le')) / 2
            requests.append({
                "insertText": {
                    "location": {
                        "index": start
                    },
                    "text": message.content + "\n\n"
                }
            })
            start += len_message + 2
            for attachment in message.attachments:
                len_attachment = len(attachment.url.encode('utf-16-le')) / 2
                if attachment.width > 450:
                    doc_width = 450
                else:
                    doc_width = attachment.width
                requests.append({
                    "insertInlineImage": {
                        "location": {
                            "index": start
                        },
                        "uri": attachment.url,
                        "objectSize": {
                            "width": {
                                "magnitude": doc_width,
                                "unit": "PT"
                            }
                        }
                    }
                })
                start += 1
                requests.append({
                    "insertText": {
                        "location": {
                            "index": start
                        },
                        "text": attachment.url + "\n\n"
                    }
                })
                requests.append({
                    "updateTextStyle": {
                        "range": {
                            "startIndex": start,
                            "endIndex": start + len_attachment
                        },
                        "textStyle": {
                            "link": {
                                "url": attachment.url
                            }
                        },
                        "fields": "link"
                    }
                })
                start += len_attachment + 2
            requests.append({
                "insertText": {
                    "location": {
                        "index": start
                    },
                    "text": "--------------------\n\n"
                }
            })
            start += 22
        result = service.documents().batchUpdate(documentId=doc_copy_id,
                                                 body={"requests": requests}).execute()
        self.bot.logger.info(f"Document created: {doc_copy_link}")
        await ctx.send(f"Created document with title: <{doc_copy_link}>\n"
                       f"This channel will delete in 10 minutes (not really).")
        # await asyncio.sleep(15)
        # await ctx.send(f"In real life, I would now delete this channel ({channel}).")


def setup(bot):
    bot.add_cog(General(bot))
