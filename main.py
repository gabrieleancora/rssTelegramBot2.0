import requests
import praw
import re
from time import sleep


# Reddit Auth Constants
BOT_ID = ''         # The bot ID
BOT_SECRET = ''     # The bot secret token
# Telegram Constants
TG_BOT_TOKEN = ''
TG_CHANNEL_ID = ''

LATEST_MANGA_LIST = [''] * 25
PROCESSED_REQUESTS = [''] * 25
REQUESTS_INDEX = 0
MANGA_INDEX = 0

def send_message(message):
    requests.get(f'https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage?chat_id={TG_CHANNEL_ID}&text={message}')

def main():
    try:
        global MANGA_INDEX, LATEST_MANGA_LIST, PROCESSED_REQUESTS, REQUESTS_INDEX
        # Reads the titles file
        fileL = open("lista.txt", "r+")
        contenutoF = fileL.read()
        MANGA_LIST = contenutoF.split(';')

        redditC = praw.Reddit(
            client_id = BOT_ID,
            client_secret = BOT_SECRET,
            user_agent = 'TelegramAlert/0.1'
        )
        mangaSubreddit = redditC.subreddit('manga')
        for submission in mangaSubreddit.new(limit=50):
            # I check if it's a release post
            if "[DISC]" in submission.title.upper():
                titleStripped = submission.title.upper().replace("[DISC]", "")
                titleStripped = re.sub(r'[^A-Za-z0-9 ]+', '', titleStripped)
                titleStripped = titleStripped.lower()
                if any(titolo in titleStripped for titolo in MANGA_LIST):
                    # I check if I haven't already checked a post with the same ID
                    if submission.id not in LATEST_MANGA_LIST:
                        print("Alert for " + submission.title)
                        # creo e mando il messaggio
                        urlCompleto = "https://www.reddit.com" + submission.permalink
                        messaggio = 'New manga chapter: ' + submission.title + '\n' + urlCompleto
                        send_message(messaggio)
                        # I save the ID to avoid duplicates
                        LATEST_MANGA_LIST[MANGA_INDEX] = submission.id
                        MANGA_INDEX += 1
                        if(MANGA_INDEX > 24):
                            print("Reset manga index")
                            MANGA_INDEX = 0

        # I read the received messages
        messaggiRaw = requests.get(f'https://api.telegram.org/bot{TG_BOT_TOKEN}/getUpdates?chat_id={TG_CHANNEL_ID}')
        messaggiDecoded = messaggiRaw.json()
        for messaggio in messaggiDecoded['result']:
            # I check that the message is from the correct chat and that I haven't already processed it
            if messaggio['update_id'] not in PROCESSED_REQUESTS:
                idCanale = str(messaggio['message']['chat']['id'])
                if idCanale == TG_CHANNEL_ID:
                    if messaggio['message']['text'].startswith('/addmanga'):
                        # If it's a correct command, I extract the manga name and I add it to the list
                        posSpazio = messaggio['message']['text'].find(' ')
                        nomeManga = messaggio['message']['text'][posSpazio:].lower().strip()
                        if len(nomeManga) > 0 and posSpazio != -1:
                            publicMsg = "Aggiungo " + nomeManga
                            toWrite = ";" + nomeManga
                            fileL.write(toWrite)
                            PROCESSED_REQUESTS[REQUESTS_INDEX] = messaggio['update_id']
                            REQUESTS_INDEX += 1
                            print(publicMsg)
                            send_message(publicMsg)
                            if(REQUESTS_INDEX > 24):
                                print("Reset requests index")
                                REQUESTS_INDEX = 0

    except Exception as e:
        print('There was an exception:\n' + str(e))
    finally:
        print('Ending now')

if __name__ == "__main__":
    while(True):
        main()
        print('Sleeping for 20 mins')
        sleep(20 * 60)
