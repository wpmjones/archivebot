.. Discord Archive Bot documentation master file, created by
   sphinx-quickstart on Mon Jul  1 01:58:24 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Discord Archive Bot's documentation!
===============================================

This bot was created to archive Discord channels to Google Docs for later retrieval.  The
only two commands are `/archive` and `/search`.

Pre-requisites
--------------

Turn on the Drive API
 - Navigate to https://developers.google.com/drive/api/v3/quickstart/python
 - Click the Enable the Drive API button
 - Click the Download Client Configuration button
 - Save credentials.json to the same folder where archivebot.py is located

Install the Google Client Library

    pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib

Invite the bot to your Discord server by clicking `this link <https://discordapp.com/oauth2/authorize?client_id=593878554446659594&scope=bot&permissions=522320>`_

The first time you issue a command, it will take you to a website where you select your
Google Account and authorize the access by the bot. This process creates a file in the bot
folder called token.pickle.  As long as you do not delete this file, you should not need
to go through this step again.


Commands
========

.. py:function:: archive(document_name)

    Archives the current channel.

    This function performs the following tasks:
    * Creates a new Google Doc (using a template)
    * Names the Doc using the channel name or the document name specified
    * Copies all messages from the channel to the Doc
    * Provides a link to the Doc
    * Waits 10 minutes, then deletes the Discord channel

    :param document_name: [Optional] Desired document name if different than the channel name

.. py:function:: search(search_str)

    Searches your Google Docs for the string you specify.  Searches both the title and body.

    :param search_str: Text to find in document