from bs4 import BeautifulSoup as bs
import datetime
import requests
import time

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"

import json
cred = json.load(open('credentials.json', 'r'))
log_channel = cred['log']

from telethon import TelegramClient, events, sync
tgClient = TelegramClient('1337xrssbot-session', cred['tg_id'], cred['tg_hash'])
tgClient.start()

import pymongo
monClient = pymongo.MongoClient(cred['mongodb_url'])
db = monClient.RSS1337
my_collection = db['1337x']

def download(dict_in_use, Title):
    checkVar = True
    incl_list = dict_in_use['INC']
    excl_list = dict_in_use['EXC']
    if incl_list:
        checkVar = False
        for Item in incl_list:
            if Item in Title:
                checkVar = True
    if excl_list:
        for Item in excl_list:
            if Item in Title:
                return False
    return checkVar

def goSoup(url):
    page = requests.get(url['URL'], headers={"User-Agent": USER_AGENT})
    soup = bs(page.content, "html.parser")
    columns = soup.find_all("td", class_="coll-1 name")
    for column in columns:
        torrent = getDict(column.find("a", class_="").get("href"))
        if my_collection.find_one({'ID' : torrent['ID']}):
            break
        else:
            if not download(url, torrent['Title']):
               continue
            time.sleep(2)
            tgClient.parse_mode = 'html'
            tgClient.send_message(url['GID'], '{} <code>{}</code>\n\n<b>ID:</b> <code>{}</code>\n<b>Name:</b> <code>{}</code>\n\n<code>1337x.to</code>'.format(url['COM'], torrent['Link'], torrent['ID'], torrent['Title']))
            time.sleep(2)
            my_collection.insert_one(torrent)
            print(torrent['Title'])

def getDict(url):
    page = requests.get("https://1337x.to" + url, headers={"User-Agent": USER_AGENT})
    soup = bs(page.content, "html.parser")
    guid = url.split("/")[2]
    name = soup.find('title').get_text()[9:-16]
    magnet = soup.find("div", class_="col-9 page-content").li.a.get('href')
    return {'ID': int(guid), 'Title': name, 'Link': magnet}

config_file = json.load(open('config.json','r'))

tgClient.send_message(log_channel, 'TeleRG started.')

import signal
run = True
def sigterm_handler(signum, frame):
    global run
    run = False
    tgClient.send_message(log_channel, 'SIGTERM received.')

signal.signal(signal.SIGTERM, sigterm_handler)

while True:
    fuc = False
    for i in config_file:
        goSoup(i)
    print("Entering sleep for 30 minutes.")
    for i in range(180):
        if run:
            time.sleep(10)
        else:
            print('SIGTERM received. Did not enter sleep.')
            print('Exiting...')
            fuc = True
            break
    if fuc:
        break
    print("Exiting sleep.")

tgClient.send_message(log_channel, 'TeleRG exited gracefully.')
