import requests
import praw
import re
import configparser
import os
from time import sleep
from datetime import datetime

# DO NOT FILL THE TOKENS HERE
# Reddit Auth
REDDIT_BOT_ID = ''         # The bot ID
REDDIT_BOT_SECRET = ''     # The bot secret token
# Telegram
TG_BOT_TOKEN = ''
TG_CHANNEL_ID = ''

# If you have to check a lot of manga or you are getting duplicates, increase this number
MAX_LIST_SIZE = 25
# Time in minutes between each check
REFRESH_TIME = 20

# Don't touch! c:
LATEST_MANGA_LIST = [''] * MAX_LIST_SIZE
MANGA_INDEX = 0
TG_OFFSET_ID = 0

def send_message(message):
    requests.get(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage?chat_id={TG_CHANNEL_ID}&text={message}&parse_mode=Markdown")

def consolePrint(message):
    header = "[" + datetime.now().strftime("%d-%m-%Y %H:%M:%S") + "] "
    print(header + message)

def main():
    try:
        global MANGA_INDEX, LATEST_MANGA_LIST, PROCESSED_REQUESTS, REQUESTS_INDEX, TG_OFFSET_ID
        MANGA_LIST = []
        # Read the titles from the file, removing the newlines
        with open('list.txt', 'r') as listFile:
            for line in listFile:
                MANGA_LIST.append(line.replace('\n',''))
        # Creates the reddit client
        redditC = praw.Reddit(
            client_id = REDDIT_BOT_ID,
            client_secret = REDDIT_BOT_SECRET,
            user_agent = 'TelegramAlert/0.4'
        )
        # The manga subreddit. 
        mangaSubreddit = redditC.subreddit('manga')
        for submission in mangaSubreddit.new(limit=50):
            # I check if it's a release post
            if "[DISC]" in submission.title.upper():
                # I strip all the strange characters 
                titleStripped = submission.title.upper().replace("[DISC]", "")
                titleStripped = re.sub(r'[^A-Za-z0-9 ]+', '', titleStripped)
                titleStripped = titleStripped.lower()
                if any(titleStripped in savedTitle for savedTitle in MANGA_LIST):
                    # I check if I haven't already checked a post with the same ID
                    if submission.id not in LATEST_MANGA_LIST:
                        consolePrint("Alert for " + submission.title)
                        # I create and send the message
                        completeUrl = 'https://www.reddit.com' + submission.permalink
                        message = "New manga chapter: " + submission.title + "\n" + completeUrl
                        send_message(message)
                        # I save the ID to avoid duplicates
                        LATEST_MANGA_LIST[MANGA_INDEX] = submission.id
                        MANGA_INDEX += 1
                        if(MANGA_INDEX > (MAX_LIST_SIZE - 1)):
                            consolePrint("Reset manga index")
                            MANGA_INDEX = 0

        # I read the received messages
        messaggiRaw = requests.get(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/getUpdates?chat_id={TG_CHANNEL_ID}&offset={TG_OFFSET_ID}")
        messaggiDecoded = messaggiRaw.json()
        for message in messaggiDecoded['result']:
            # I save the offset id to avoid requesting the same message twice
            TG_OFFSET_ID = message['update_id'] + 1
            if message['message']['text'].startswith('/addmanga'):
                # If it's a correct command, I extract the manga name and I add it to the file
                spacePosition = message['message']['text'].find(' ')
                mangaName = message['message']['text'][spacePosition:].lower().strip()
                if len(mangaName) > 0 and spacePosition != -1:
                    # Writing in the file
                    with open('list.txt', 'a') as listFile:
                        listFile.write(mangaName)
                        listFile.write("\n")
                    # I reload the manga_list variable to include the newest addition
                    MANGA_LIST = []
                    with open('list.txt', 'r') as listFile:
                        for line in listFile:
                            MANGA_LIST.append(line.replace('\n',''))
                    publicMsg = "Added the manga `" + mangaName + "` to the alert list."
                    consolePrint(publicMsg)
                    send_message(publicMsg)
                    
    except Exception as e:
        print("There was an exception:\n" + str(e))
        send_message("The bot crashed, please check the console for more informations about the error.")
        exit(1)
    finally:
        consolePrint('Ending now')

if __name__ == "__main__":
    # Check for the old list file and converts it to the newer list file
    if os.path.isfile('lista.txt'):
        print("Converting the old list file to a newer, v2, format.")
        os.rename('lista.txt','oldList.txt')
        oldMangaList = ""
        with open('oldList.txt', 'r') as oldMangaListFile:
            oldMangaList = oldMangaListFile.read()
        oldMangaListArray = oldMangaList.split(';')
        with open('list.txt','w') as newList:
            for manga in oldMangaListArray:
                if len(manga.strip()) > 0:
                    newList.write(manga)
                    newList.write("\n")
    
    # Check for config file and loads it
    if os.path.isfile('auth.ini'):
        config = configparser.ConfigParser()
        config.read('auth.ini')
        TG_BOT_TOKEN = config['Telegram']['TG_BOT_TOKEN']
        TG_CHANNEL_ID = config['Telegram']['TG_CHANNEL_ID']
        REDDIT_BOT_ID = config['Reddit']['REDDIT_BOT_ID']
        REDDIT_BOT_SECRET = config['Reddit']['REDDIT_BOT_SECRET']
        if TG_BOT_TOKEN == "" or TG_CHANNEL_ID == "" or REDDIT_BOT_ID == "" or REDDIT_BOT_SECRET == "":
            print("Please fill all the required informations! Only the Mangadex part is optional!")
            exit(1)
        consolePrint("Program initialized, starting the main loop.")
        # The "main" loop
        while(True):
            main()
            consolePrint(f"Sleeping for {REFRESH_TIME} mins")
            sleep(REFRESH_TIME * 60)
    else:
        print("Error: the file auth.ini wasn't found. Please insert all the required fields and rerun the program.")
        with open('auth.ini', 'w') as f:
            f.write("[Telegram]\nTG_BOT_TOKEN = \nTG_CHANNEL_ID = \n\n[Reddit]\nREDDIT_BOT_ID = \nREDDIT_BOT_SECRET = \n\n[Mangadex]\nMD_USERNAME = \nMD_PASSWORD = \n")
