from re import sub
import requests
import praw
from time import sleep
import pprint

# Reddit Auth Constants
BOT_ID = ''         # The bot ID
BOT_SECRET = ''     # The bot secret token

LATEST_MANGA_LIST = [''] * 25
PROCESSED_REQUESTS = [''] * 25
REQUESTS_INDEX = 0
MANGA_INDEX = 0


# Telegram Constants
TG_BOT_TOKEN = ''
TG_CHANNEL_ID = ''

def send_message(message):
    requests.get(f'https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage?chat_id={TG_CHANNEL_ID}&text={message}')

def main():
    try:
        global MANGA_INDEX, LATEST_MANGA_LIST, PROCESSED_REQUESTS, REQUESTS_INDEX
        #legge il file con i titoli
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
            #controllo se è una release manga
            if "[DISC]" in submission.title.upper():
                if any(titolo in submission.title.lower() for titolo in MANGA_LIST):
                    # se l'id non è presente nella lista dei post recenti
                    if submission.id not in LATEST_MANGA_LIST:
                        print("Avviso per " + submission.title)
                        # creo e mando il messaggio
                        urlCompleto = "https://www.reddit.com" + submission.permalink
                        urlMobile = "https://gabrieledinuovo.it/reddirect.html?redd=" + submission.id
                        messaggio = submission.title + '\n' + urlCompleto + '\n\n' + urlMobile
                        send_message(messaggio)
                        # salva l'id per evitare duplicati
                        LATEST_MANGA_LIST[MANGA_INDEX] = submission.id
                        MANGA_INDEX += 1
                        if(MANGA_INDEX > 24):
                            print("reset dell'index manga")
                            MANGA_INDEX = 0

        #leggo i messaggi ricevuti
        messaggiRaw = requests.get(f'https://api.telegram.org/bot{TG_BOT_TOKEN}/getUpdates?chat_id={TG_CHANNEL_ID}')
        messaggiDecoded = messaggiRaw.json()
        for messaggio in messaggiDecoded['result']:
            #controllo di non averlo già processato e che venga dal mio gruppo
            if messaggio['update_id'] not in PROCESSED_REQUESTS:
                idCanale = str(messaggio['message']['chat']['id'])
                if idCanale == TG_CHANNEL_ID:
                    if messaggio['message']['text'].startswith('/addmanga'):
                        #se è il comando giusto, estraggo il nome del manga e lo aggiungo alla lista
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
                                print("reset dell'index richieste")
                                REQUESTS_INDEX = 0

    except Exception as e:
        print('There was an exception:\n' + str(e))
    finally:
        print('Ending now')

if __name__ == "__main__":
    while(True):
        main()
        print('sleeping for 20 mins')
        sleep(20 * 60)
