import feedparser
from datetime import datetime
import time

import json
cred = pickle.load(open('credentials.json', 'rb'))
log_channel = cred['log']

from telethon import TelegramClient, events, sync
tgClient = TelegramClient('rssbot-session', cred['tg_id'], cred['tg_hash'])
tgClient.start()

import pymongo
monClient = pymongo.MongoClient(cred['mongodb_url'])
db = monClient.TeleRG
my_collection = db['TeleRG']

def download(dict_in_use, Title):
    checkVar = True
    incl_list = dict_in_use['incl']
    excl_list = dict_in_use['excl']
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
    
def tg_mongo_run(dict_in_use, entry, time_grab):
    site_name = dict_in_use['url'].split('/')[2]
    tgClient.parse_mode = 'html'    
    messageObject = tgClient.send_message(dict_in_use['id'], "<b>"+ dict_in_use['command'] + 
                                        "</b> <code>" + entry.link + "</code> <b>\n\nName: </b><code>" +  
                                        entry.title + "</code><b>\nPublished: </b><code>" + 
                                        datetime.fromtimestamp(time.mktime(entry.published_parsed)).strftime("%Y-%m-%d %H:%M:%S") + 
                                        '\n\n' + site_name + '</code>\ncc: shashwatverma')
    stor_dict = {
            'Website' : site_name,
            'Time_Added' : time_grab,
            'Message_Link' : "https://t.me/c/" + str(messageObject.peer_id.channel_id) + "/" + str(messageObject.id),
            'Title' : entry.title,
            'Identifier' : entry.guid,
            'Published' : datetime.fromtimestamp(time.mktime(entry.published_parsed)),
            'Link' : entry.link,
            }
    my_collection.insert_one(stor_dict)
    print(entry.title)

def main(eid, info_list):
    dict_in_use = info_list[eid]
    rss_feed = feedparser.parse(dict_in_use['url'])
    time_grab = datetime.now()
    for entry in rss_feed.entries:
        if my_collection.find_one({'Identifier' : entry.guid}):
            break
        else:
            if not download(dict_in_use, entry.title):
               continue
            tg_mongo_run(dict_in_use, entry, time_grab)

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
    for i in range(0,len(config_file)):
        main(i, config_file)
    print("Entering sleep for 60 seconds.")
    for i in range(5):
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
