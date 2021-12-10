# rssTelegramBot2.0
v1 (now private) is not going to be updated anymore since reddit rate limited me...

## Prerequisites
- Python 3
- [praw](https://github.com/praw-dev/praw)

## Usage:
- Create a new bot on Telegram. I'm super lazy and I created a very basic one, added to a group with only me and then disabled the `/setjoingroups` option.
- Add this exact two commands for make it work correctly:  
`addmanga - Adds a new manga to the interested manga list`  
~~removemanga - Removes a manga from the list of interests~~ Not implemented yet, but maybe you can add it as futureproof?
- Get the API Token for the bot
- Obtain the channel ID for the group/chat where you want the bot to send the messages to
- Create a reddit script from https://www.reddit.com/prefs/apps/ (you must be logged in)
- Sign the reddit API terms (found here: https://www.reddit.com/wiki/api ) to avoid bans
- Download the main.py script
- Fill the missing informations in the auth.ini file (telegram channel ID, telegram bot token, reddit script ID, reddit script secret). If the file isn't present, start the program, it will generate the file for you.
- Start the bot!

No messages are sent on initialization.  
Use tmux or something similar to avoid to close the python session when you log out from the device

## Future plans:  
- [ ] move all the auth stuff to a separate file lol
- [ ] `/removemanga` to remove a manga from the list (maybe using telegram buttons to avoid "guessing" what the user wrote vs what is in the file)
- [ ] [mangadex.org](https://mangadex.org/) 'followed manga' integration using the API! (it would require to save on the bot files the username and the password tho) ([https://api.mangadex.org/swagger.html#/Feed/get-user-follows-manga-feed](https://api.mangadex.org/swagger.html#/Feed/get-user-follows-manga-feed))