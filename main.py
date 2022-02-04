import requests
import praw
from prawcore.exceptions import PrawcoreException
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
BACKOFF_RETRIES = 0

def send_message(message, markdown = False):
    message = message.replace("%", "%25")
    message = message.replace("&", "%26")
    message = message.replace("<", "%3C")
    message = message.replace(">", "%3E")
    apend = ""
    if markdown == True:
        apend = "&parse_mode=Markdown"
    requests.get(f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage?chat_id={TG_CHANNEL_ID}&text={message}{apend}")

def consolePrint(message):
    header = "[" + datetime.now().strftime("%d-%m-%Y %H:%M:%S") + "] "
    print(header + message)

def main():
    try:
        global MANGA_INDEX, LATEST_MANGA_LIST, PROCESSED_REQUESTS, REQUESTS_INDEX, TG_OFFSET_ID, BACKOFF_RETRIES
        MANGA_LIST = []
        if BACKOFF_RETRIES > 0:
            consolePrint(f"Sending a message to the Telegram channel to inform that the bot is back online.\nIt was offline for {BACKOFF_RETRIES} checks.")
            send_message(f"The bot couldn't check for new manga for {BACKOFF_RETRIES} times because of connection problems.")
            BACKOFF_RETRIES = 0

        # Read the titles from the file, removing the newlines
        with open('list.txt', 'r') as listFile:
            for line in listFile:
                MANGA_LIST.append(line.replace('\n',''))
        # Creates the reddit client
        redditC = praw.Reddit(
            client_id = REDDIT_BOT_ID,
            client_secret = REDDIT_BOT_SECRET,
            user_agent = 'TelegramAlert/0.5.1'
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
                if any(savedTitle in titleStripped for savedTitle in MANGA_LIST):
                    # I check if I haven't already checked a post with the same ID
                    if submission.id not in LATEST_MANGA_LIST:
                        consolePrint("Alert for " + submission.title)
                        # I create and send the message
                        completeUrl = "https://www.reddit.com" + submission.permalink
                        message = f"New manga chapter: {submission.title}\n{completeUrl}"
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
                    send_message(publicMsg, True)
            
            elif message['message']['text'].startswith('/removemanga'):
                # If it's a correct command, I extract the manga name and I remove it from the file
                spacePosition = message['message']['text'].find(' ')
                mangaName = message['message']['text'][spacePosition:].lower().strip()
                if len(mangaName) > 0 and spacePosition != -1:
                    publicMsg = "The manga wasn't found in the alert list."
                    try:
                        # I find the index of the manga to remove
                        toRemove = MANGA_LIST.index(mangaName)
                        with open("list.txt", "w") as listFile:
                            i = 0
                            for manga in MANGA_LIST:
                                if i != toRemove:
                                    listFile.write(manga)
                                    listFile.write("\n")
                                i = i + 1
                        # I reload the manga_list variable to remove the manga from the alerts
                        MANGA_LIST = []
                        with open('list.txt', 'r') as listFile:
                            for line in listFile:
                                MANGA_LIST.append(line.replace('\n',''))
                        publicMsg = "The manga `" + mangaName + "` was removed from the alert list."
                    except ValueError as e:
                        # If the title isn't found, I print the closes matches.
                        closer_value_list = [needle for needle in MANGA_LIST if mangaName in needle]
                        if len(closer_value_list) > 0:
                            publicMsg = "The manga wasn't found, the closest entries are:\n```\n"
                            for el in closer_value_list:
                                publicMsg = publicMsg + el + "\n"
                            publicMsg = publicMsg + "```"
                    finally:
                        send_message(publicMsg, True)
                        consolePrint(publicMsg)
                    
            elif message['message']['text'].startswith('/mangalist'):
                # "Simply" sends a list of the interesting manga.
                # Please don't make the message longer than 3000 characters because Telegram is going to refuse it.
                messageToSend = "List of manga:\n```\n"
                for manga in MANGA_LIST:
                    messageToSend = messageToSend + manga + "\n"
                messageToSend = messageToSend + "```"
                send_message(messageToSend, True)            
                consolePrint("Sending a list of all registered manga alerts.")

    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        consolePrint(f"There was a connection error, retrying after {REFRESH_TIME} minutes.")
        consolePrint(f"The exception was: {e}")
        BACKOFF_RETRIES += 1
        return
    except PrawcoreException as e:
        consolePrint(f"There was a reddit connection error, retrying after {REFRESH_TIME} minutes")
        consolePrint(f"The exception was: {e}")
        BACKOFF_RETRIES += 1
        return
    except Exception as e:
        consolePrint("There was an exception:\n" + str(e))
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
        send_message(f"Bot initialized successfully!\nThe refresh interval is currently set at {REFRESH_TIME} minutes.")
        # The "main" loop
        while(True):
            main()
            consolePrint(f"Sleeping for {REFRESH_TIME} mins")
            sleep(REFRESH_TIME * 60)
    else:
        print("Error: the file auth.ini wasn't found. Please insert all the required fields and rerun the program.")
        with open('auth.ini', 'w') as f:
            f.write("[Telegram]\nTG_BOT_TOKEN = \nTG_CHANNEL_ID = \n\n[Reddit]\nREDDIT_BOT_ID = \nREDDIT_BOT_SECRET = \n\n[Mangadex]\nMD_USERNAME = \nMD_PASSWORD = \n")
