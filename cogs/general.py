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

    @staticmethod
    def read_paragraph_element(paragraph):
        text_run = paragraph.get("textRun")
        if not text_run:
            return ""
        return text_run.get("content")

    @commands.command(name="list")
    async def archive_list(self, ctx):
        await ctx.send("The full list of archived documents can be found here. "
                       "Please do not share this link outside of the Scounting team.\n"
                       "https://drive.google.com/open?id=1kXSqsStCNbcBLwqNUvkKVo4qXDljQCqD")

    @commands.command(name="build")
    async def build(self, ctx):
        msg = await ctx.send("One moment while I crack the archives and search for your request...")
        results = drive_service.files().list(pageSize=1000,
                                             fields="nextPageToken, files(id, name, mimeType, trashed)").execute()
        items = results.get('files', [])
        conn = self.bot.pool
        sql = "SELECT doc_link FROM rcs_archives"
        rows = await conn.fetch(sql)
        links = [row['doc_link'] for row in rows]
        print(links)
        for item in items:
            if item['id'] in links:
                continue
            await msg.edit(content=msg.content + ".")
            if item['trashed'] or item['mimeType'] != "application/vnd.google-apps.document":
                continue
            if "ARCHIVE" in item['name']:
                try:
                    doc = service.documents().get(documentId=item['id']).execute()
                    doc_content = doc.get('body').get('content')
                    content = ""
                    for element in doc_content:
                        if "paragraph" in element:
                            paragraphs = element.get("paragraph").get("elements")
                            for paragraph in paragraphs:
                                content += self.read_paragraph_element(paragraph)
                    sql = ("INSERT INTO rcs_archives (doc_title, doc_link, doc_body) "
                           "VALUES ($1, $2, $3)")
                    await conn.execute(sql, item['name'], item['id'], content)
                    self.bot.logger.info(f"Added {item['name']} to database")
                except:
                    self.bot.logger.exception(f"Failed on {item['name']}")

    @commands.command(name="search")
    async def search(self, ctx, *, search_str):
        if search_str == "list":
            await ctx.invoke(self.archive_list)
            return
        msg = await ctx.send("One moment while I crack the archives and search for your request...")
        conn = self.bot.pool
        sql = "SELECT doc_title, doc_link, doc_body FROM rcs_archives WHERE doc_title ~* $1 or doc_body ~* $2"
        rows = await conn.fetch(sql, search_str, search_str)
        file_list = ""
        if not rows:
            self.bot.logger.warning(f"No files found for {search_str}")
            await msg.edit(content=f"No files found with the text {search_str} in the title or body.")
        for row in rows:
            file_list += f"{row['doc_title']} <https://docs.google.com/document/d/{row['doc_link']}/edit>\n"
        if file_list != "":
            content = "**Files found:**\n" + file_list
            self.bot.logger.info(f"Reported:\n{file_list}")
            await msg.edit(content=content)

    @commands.command(name="archive")
    @commands.has_any_role("Council", "RCS Scouts")
    async def archive(self, ctx, *, channel: str = None):
        """Archives the current channel.

        This function performs the following tasks:
        * Creates a new Google Doc (using a template)
        * Names the Doc using the channel name or the document name specified
        * Copies all messages from the channel to the Doc
        * Provides a link to the Doc
        * Waits 10 minutes, then deletes the Discord channel

        Parameters
        ----------
        channel : str, optional
            Desired document name if different than the channel name.
        """
        if not channel:
            channel = ctx.channel.name
        now = datetime.utcnow().strftime("%d %B %Y, %H:%M:%S")
        len_now = (len(now.encode('utf-16-le')) / 2) + 4
        doc_name = f"ARCHIVE - {channel.replace('-',' ').title()}"
        doc_name = doc_name.replace("   ", " - ")
        len_doc_name = len(doc_name.encode('utf-16-le')) / 2
        msg = await ctx.send(f"One moment while I create an archive named {doc_name}.")
        # The following template a public Doc and is important for proper formatting of archived channels.
        template_id = "15iTyuU5lax8dJiE1ur9MDnIMm3YCFnlfSXH3pSzJzhk"
        body = {"name": doc_name}
        new_doc = drive_service.files().copy(fileId=template_id, body=body).execute()
        doc_copy_id = new_doc.get('id')
        doc_copy_link = f"https://docs.google.com/document/d/{doc_copy_id}/edit"
        doc_body = ""
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
        doc_body += f"{doc_name}\n{now} GMT\n\n"
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
            doc_body += message.author.display_name + "\n"
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
            doc_body += created + "\n\n"
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
            doc_body += message.content + "\n\n"
            start += len_message + 2
            for attachment in message.attachments:
                len_attachment = len(attachment.url.encode('utf-16-le')) / 2
                try:
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
                    doc_body += attachment.url + "\n\n"
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
                except (TypeError, AttributeError) as e:
                    # This should handle non-image attachments and effectively skip them.
                    self.bot.logger.error(f"Error on attachment. Including link only.\n{attachment.url}\n{e}")
                    requests.append({
                        "insertText": {
                            "location": {
                                "index": start
                            },
                            "text": attachment.url + "\n\n"
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
        conn = self.bot.pool
        sql = ("INSERT INTO rcs_archives (doc_title, doc_link, doc_body) "
               "VALUES ($1, $2, $3)")
        await conn.execute(sql, doc_name, doc_copy_id, doc_body)
        self.bot.logger.info(f"Document created: {doc_copy_link}")
        await msg.edit(content=f"Created document with title: {doc_name}\n<{doc_copy_link}>\n"
                               f"Please check that the entire document was archived properly, then issue the "
                               f"`/delete` command.")

    @commands.command(name="delete")
    @commands.has_any_role("Council")
    async def delete_channel(self, ctx):
        """Deletes the current channel."""
        def check(r, u):
            return str(r) in reactions and u.id == ctx.author.id and r.message.id == msg.id

        msg = await ctx.send("Are you sure you want to delete this channel?")
        reactions = ["🇾", "🇳"]
        for r in reactions:
            try:
                await msg.add_reaction(r)
            except:
                self.bot.logger.exception("Emoji fail")
        try:
            r, u = await self.bot.wait_for("reaction_add", check=check, timeout=60.0)
        except asyncio.TimeoutError:
            await ctx.message.delete()
            await msg.delete()
            msg = await ctx.send("Timeout - Deletion Cancelled")
            await msg.delete(delay=60.0)
            return
        if reactions.index(str(r)) == 1:
            await ctx.message.delete()
            await msg.delete()
            msg = await ctx.send("Deletion cancelled by user")
            await msg.delete(delay=15.0)
            return
        if reactions.index(str(r)) == 0:
            self.bot.logger.info(f"{ctx.channel} on {ctx.guild} deleted by {ctx.author}")
            await ctx.channel.delete(reason="Delete command from Archive Bot")

@staticmethod
async def send_text(channel, text, block=None):
    """ Sends text to channel, splitting if necessary """
    if len(text) < 2000:
        if block:
            await channel.send(f"```{text}```")
        else:
            await channel.send(text)
    else:
        coll = ""
        for line in text.splitlines(keepends=True):
            if len(coll) + len(line) > 1994:
                # if collecting is going to be too long, send  what you have so far
                if block:
                    await channel.send(f"```{coll}```")
                else:
                    await channel.send(coll)
                coll = ""
            coll += line
        await channel.send(coll)


def setup(bot):
    bot.add_cog(General(bot))
