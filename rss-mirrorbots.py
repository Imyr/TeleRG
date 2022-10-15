import sys
import json
import time
import signal
import pymongo
import feedparser
from datetime import datetime
from telethon import TelegramClient, sessions

def sigterm_handler(signum, frame):
    global run
    run = False
    tgClient.send_message(log_channel, 'SIGTERM received.')

def checkVar(dict_in_use, Title):
    c = True
    incl_list = dict_in_use['incl']
    excl_list = dict_in_use['excl']
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
    
def post(dict_in_use, entry, time_grab):
    site_name = dict_in_use['url'].split('/')[2] 
    try:
        messageObject = tgClient.send_message(dict_in_use['id'], "<b>"+ dict_in_use['command'] + 
                                            "</b> <code>" + entry.link + "</code> <b>\n\nName: </b><code>" +  
                                            entry.title + "</code><b>\nPublished: </b><code>" + 
                                            datetime.fromtimestamp(time.mktime(entry.published_parsed)).strftime("%Y-%m-%d %H:%M:%S") + 
                                            '</code>\n\n<code>' + site_name + '</code>')
        messageLink = "https://t.me/c/" + str(messageObject.peer_id.channel_id) + "/" + str(messageObject.id)                                            
        Status = "Passed"
    except:
        print("Sending message failed:", entry.guid)
        messageLink = None
        Status = "Failed"
    stor_dict = {
            'Website' : site_name,
            'Time_Added' : time_grab,
            'Message_Link' : messageLink,
            'Title' : entry.title,
            'Identifier' : entry.guid,
            'Published' : datetime.fromtimestamp(time.mktime(entry.published_parsed)),
            'Link' : entry.link,
            'Status': Status
            }
    try:
        my_collection.insert_one(stor_dict)
    except:
        print("Insertion into database failed:", entry.guid)
    print(entry.title)

def main(eid, info_list):
    dict_in_use = info_list[eid]
    try:    
        rss_feed = feedparser.parse(dict_in_use['url'])
    except:
        print("Couldn't parse RSS feed:", dict_in_use['url'])

    time_grab = datetime.now()
    for entry in rss_feed.entries:
        if my_collection.find_one({'Identifier' : entry.guid}):
            break
        else:
            if not checkVar(dict_in_use, entry.title):
               continue
            post(dict_in_use, entry, time_grab)

try:
    cred = json.load(open('credentials.json', 'r'))
except:
    sys.exit("Couldn't open credentials.json.")
log_channel = cred['log']

try:
    config_file = json.load(open('config.json','r'))
except:
    sys.exit("Couldn't open config.json.")    

tgClient = TelegramClient(sessions.StringSession(cred["session_string"]), cred['tg_id'], cred['tg_hash'])
tgClient.start()
tgClient.parse_mode = 'html'

monClient = pymongo.MongoClient(cred['mongodb_url'])
db = monClient.TeleRG
my_collection = db['TeleRG']

signal.signal(signal.SIGTERM, sigterm_handler)


tgClient.send_message(log_channel, 'TeleRG started.')
run = True
while True:
    stop = False
    for i in range(0,len(config_file)):
        main(i, config_file)
    print("Entering sleep for 60 seconds.")
    for i in range(59):
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
tgClient.send_message(log_channel, 'TeleRG exited gracefully.')
