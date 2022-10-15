import sys
import json
import time
import signal
import pymongo
import requests
from bs4 import BeautifulSoup as bs
from telethon import TelegramClient, sessions

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

def sigterm_handler(signum, frame):
    global run
    run = False
    tgClient.send_message(log_channel, 'SIGTERM received.')

def checkVar(dict_in_use, Title):
    c = True
    incl_list = dict_in_use['INC']
    excl_list = dict_in_use['EXC']
    if incl_list:
        c = False
        for Item in incl_list:
            if Item in Title:
                c = True
    if excl_list:
        for Item in excl_list:
            if Item in Title:
                return False
    return c

def getDict(url):
    try:
        page = requests.get("https://1337x.to" + url, headers={"User-Agent": USER_AGENT})
    except:
        print("Couldn't open URL:", url)
        raise
    soup = bs(page.content, "html.parser")
    guid = url.split("/")[2]
    name = soup.find('title').get_text()[9:-16]
    try:
        magnet = soup.find("div", class_="col-9 page-content").li.a.get('href')
    except:
        print("Couldn't parse page:", url)
        raise
    return {'ID': int(guid), 'Title': name, 'Link': magnet}

def goSoup(url):
    try:
        page = requests.get(url['URL'], headers={"User-Agent": USER_AGENT})
    except:
        print("Couldn't open URL:", url['URL'])
        raise
    soup = bs(page.content, "html.parser")
    try:
        columns = soup.find_all("td", class_="coll-1 name")
    except:
        print("Couldn't parse page:", url['URL'])
        raise
    for column in columns:
        torrent = getDict(column.find("a", class_="").get("href"))
        if my_collection.find_one({'ID' : torrent['ID']}):
            break
        else:
            if not checkVar(url, torrent['Title']):
               continue
            try:
                tgClient.send_message(url['GID'], '{} <code>{}</code>\n\n<b>ID:</b> <code>{}</code>\n<b>Name:</b> <code>{}</code>\n\n<code>1337x.to</code>'.format(url['COM'], torrent['Link'], torrent['ID'], torrent['Title']))
            except:
                print("Sending message failed:", torrent['ID'])
                raise
            try:
                my_collection.insert_one(torrent)
            except:
                print("Insertion into database failed:", torrent['ID'])
                raise
            print(torrent['Title'])

try:
    cred = json.load(open('credentials.json', 'r'))
except:
    sys.exit("Couldn't open credentials.json.")
log_channel = cred['log']

try:
    config_file = json.load(open('config.json','r'))
except:
    sys.exit("Couldn't open config.json.")  

tgClient = TelegramClient(sessions.StringSession(cred['session_string']), cred['tg_id'], cred['tg_hash'])
tgClient.start()
tgClient.parse_mode = 'html'

monClient = pymongo.MongoClient(cred['mongodb_url'])
db = monClient.RSS1337
my_collection = db['1337x']

signal.signal(signal.SIGTERM, sigterm_handler)


tgClient.send_message(log_channel, 'TeleRG started.')
run = True
while True:
    stop = False
    for i in config_file:
        try:
            goSoup(i)
        except Exception as e:
            print(e)
            print("Sleeping for 2 minutes before retrying...")
            time.sleep(120)
            goSoup(i)
    print("Entering sleep for 30 minutes.")
    for i in range(1800):
        if run:
            time.sleep(1)
        else:
            print('SIGTERM received. Did not enter sleep.')
            print('Exiting...')
            stop = True
            break
    if stop:
        break
    print("Exiting sleep.")
tgClient.send_message(log_channel, '1337x-TeleRG exited gracefully.')
