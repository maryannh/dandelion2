import config
import os
from dateutil.parser import parse
import requests
from pymongo import MongoClient
import datetime

client = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority")
db = client.blog

def all_content_ids(content_type):
    """ get short ids of all active content """
    if content_type == "post":
        content = config.POSTS_LABEL
    elif content_type == "page":
        content = config.PAGES_LABEL
    elif content_type == "download":
        content = config.DOWNLOADS_LABEL
    elif content_type == "link":
        content = config.LINKS_LABEL
    payload = {
        'key': config.TRELLO_KEY,
        'token': config.TRELLO_TOKEN,
        }
    url = "https://api.trello.com/1/boards/" + config.BOARD_ID + "/cards/open"
    r = requests.get(url, params=payload)
    cards = r.json()
    items = []
    for card in cards:
        labels = card["idLabels"]
        if content in labels:
            if card["dueComplete"] == True:
                item_id = card["shortLink"]
                items.append(item_id)
    return items

def add_to_db(content_type):
    """ add content to Mongo DB """
    payload = {
        'key': config.TRELLO_KEY,
        'token': config.TRELLO_TOKEN,
        }
    items = all_content_ids(content_type)
    item_loop = []
    for item_id in items:
        # content
        content_url = "https://api.trello.com/1/cards/" + item_id
        content_r = requests.get(content_url, params=payload)
        content = content_r.json()
        date = content.get("due", "NA")
        image = None
        if content_type == "post":
            # attachments
            payload = {
                'key': config.TRELLO_KEY,
                'token': config.TRELLO_TOKEN,
                'filter': 'cover'
                }
            attachments_url = "https://api.trello.com/1/cards/" + item_id + "/attachments"
            attachments_r = requests.get(attachments_url, params=payload)
            attachments = attachments_r.json()
            image = attachments[0]["url"]
        info = {
                "date": date,
                "item_id": item_id,
                "title": content.get("name", "NA"),
                "image": image,
                "text": content.get("desc", "NA"),
                "type": content_type,
            }
        # add to db
        post_id = db.content.insert_one(info).inserted_id
        print(post_id)
        
add_to_db("link")
