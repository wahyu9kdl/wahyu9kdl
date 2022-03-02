import tweepy
import re
import requests

from decouple import config

consumer_key = config('C_KEY')
consumer_secret = config('C_SECRET')
key = config('KEY')
secret = config('SECRET')

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(key, secret)
API = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

FILE_NAME = 'storage.txt'
try:
    f = open(FILE_NAME)
except:
    f = open(FILE_NAME, 'w+')
    text = "mentionId=''\nmessageId=[]\nmessageRead=''"
    f.write(text)
    f.close()

def read_last_seen(FILE_NAME, type):
    file_read = open(FILE_NAME, 'r')
    seen_id = file_read.read().strip()
    if type == "men":
        seen_id = re.split("(?<=mentionId=')(.*)(?=')", seen_id)
        seen_id = seen_id[1]
        if len(seen_id) == 0:
            seen_id = None
        else:
            seen_id = int(seen_id)
    elif type == "dm":
        seen_id = re.split("(?<=messageId=\[)(.*)(?=\])", seen_id)
        seen_id = seen_id[1].split(',')
        if len(seen_id[0]) == 0:
            seen_id = seen_id[0]
            
    file_read.close()
    return seen_id

def store_last_seen(FILE_NAME, seen_id, type):
    file_write = open(FILE_NAME, 'r')
    file_write = file_write.read()
    print(file_write)
    seen_id = str(seen_id)
    if type == "men":
        f = open(FILE_NAME, 'w')
        seen_id = re.sub("(?<=mentionId=')(.*)(?=')", seen_id, file_write)
        f.write(seen_id)
    elif type == "dm":
        checked = re.search("(?<=messageId=\[)(,)", file_write )
        if checked:
            file_write = re.sub("(?<=messageId=\[)(,)","",file_write)
        splitId = re.split("(?<=messageId=\[)(.*)(?=\])", file_write)
        lookId = splitId[1].split(',')
        lookId.append(seen_id)
        delimit = [",",""]
        lookId = delimit[0].join(lookId)
        splitId.insert(1, lookId)
        splitId.pop(2)
        res = delimit[1].join(splitId)
        f = open(FILE_NAME, 'r+')
        f.write(res)
        f.close()
    return

mentions = API.mentions_timeline(read_last_seen(FILE_NAME, "men"), tweet_mode='extended')
dm = API.list_direct_messages(10, tweet_mode='extended')
countMention = str(len(mentions)) + ' tweets'
countDm = str(len(dm)) + ' messages'
print({"Mentions": countMention, "DM": countDm})

for mention in reversed(mentions):
    if '#testbot' in mention.full_text.lower():
        if len(mentions) > 0 :
            print(str(mention.id) + ' - (' + mention.user.name + ') => ' + mention.full_text)
            try:
                API.update_status("@" + mention.user.screen_name + " Hi " + mention.user.name + "!\nIni id kamu => '" + str(mention.id) + "'!\nBot reply tested!", mention.id)
            except tweepy.TweepError as error:
                if error.api_code == 187:
                    print('duplicate message')
                else:
                    raise error
            store_last_seen(FILE_NAME, mention.id, "men")

for message in reversed(dm):
    dmId = str(message.id)
    seen_id = read_last_seen(FILE_NAME, "dm")
    arrDm = [dmId]
    res = [key for key, val in enumerate(seen_id) if val in set(arrDm)]
    if len(res) == 0:
        getDm = API.get_direct_message(int(dmId))
        getText = str(getDm.message_create['message_data']['text'])[0:150]
        getSender = getDm.message_create['sender_id']
        getUser = API.get_user(getSender).screen_name
        try:
            tweet = API.update_status(" Hi @" + getUser + " ! ~ your message: '" + str(getText) + "'\nBot status tested!")
            getLink = "That your tweet >.< https://twitter.com/Awfanspage/status/" + str(tweet.id)
            sendDm = API.send_direct_message(getSender,getLink)
            store_last_seen(FILE_NAME, str(sendDm.id), "dm")
        except tweepy.TweepError as error:
            if error.api_code == 187:
                # Do something special
                print('duplicate message')
            else:
                raise error
        store_last_seen(FILE_NAME, str(dmId), "dm")
