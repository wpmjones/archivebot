![Archive Bot](http://www.mayodev.com/images/archivebot128.png)

# archivebot

Archive Discords Channels to Google Docs

## /archive
**/archive <optional document name>**
Archives the channel you are in using the name of the channel (see option), provides a link to the archive doc, then 
waits 10 minutes before deleting the channel. Optional: you can include a document name after /archive if you want 
to specify a name.

## /search
**/search search string**
Searches existing Google Docs for the text specified. It will search both the title and body 
of the document, but the search is limited to archived channels housed in the Google Drive 
account. You may want to search by clan name or tag, but feel free to search for any text 
at all.

---

## Pre-requisites
Turn on the Drive API
 - Navigate to https://developers.google.com/drive/api/v3/quickstart/python
 - Click the Enable the Drive API button
 - Click the Download Client Configuration button
 - Save credentials.json to the same folder where archivebot.py is located 

Install the Google Client Library

    pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
    
Invite the bot to your Discord server

The first time you issue a command, it will take you to a website where you select your 
Google Account and authorize the access by the bot. This process creates a file in the bot 
folder called token.pickle.  As long as you do not delete this file, you should not need 
to go through this step again. 