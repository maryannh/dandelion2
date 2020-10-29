import config
import os
from dateutil.parser import parse
import requests
from pymongo import MongoClient
import datetime
import dns
import json
from validator_collection import validators, checkers

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

def imported_ids(content_type):
    """ gets a list of Trello IDs of all the content already in Mongo """
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    content = list(db.content.find({"type": content_type }))
    ids = []
    for item in content:
        ids.append(item["item_id"])
    return ids

def ids_to_import(content_type):
    """ gets a list of Trello IDs of all the content that needs to be imported """
    all_ids = all_content_ids(content_type)
    return list(set(all_content_ids(content_type)) - set(imported_ids(content_type)))

def get_credits(item_id):
    """ get custom field info from Trello """
    payload = {
                'key': config.TRELLO_KEY,
                'token': config.TRELLO_TOKEN,
                'filter': 'cover'
                }
    url = "https://api.trello.com/1/cards/" + item_id + "/customFieldItems"
    r = requests.get(url, params=payload)
    data = r.json()
    first = data[0]
    first_value = first["value"]["text"]
    second = data[1]
    second_value = second["value"]["text"]
    if checkers.is_url(first_value):
        credit_url = first_value
        credit_name = second_value
    elif checkers.is_url(second_value):
        credit_url = second_value
        credit_name = first_value
    else:
        credit_url = None
        credit_name = None
    return {
        "name": credit_name,
        "url": credit_url
    }  

def get_labels(item_id):
    payload = {
                'key': config.TRELLO_KEY,
                'token': config.TRELLO_TOKEN,
                }
    url = "https://api.trello.com/1/cards/" + item_id
    r = requests.get(url, params=payload)
    data = r.json()
    labels = data["idLabels"]
    tags = []
    subjects = []
    for label in labels:
        label_url = "https://api.trello.com/1/labels/" + label
        label_r = requests.get(label_url, params=payload)
        data = label_r.json()
        subject = None
        tag = None
        if data["color"] == "green":
            subject = data["name"]
            subjects.append(subject)
        if data["color"] == "purple":
            tag = data["name"]
            tags.append(tag)
    taxonomy = {
        "tags": tags,
        "subjects": subjects,
    }
    return taxonomy      
    
def add_to_db(content_type):
    """ add content to Mongo DB """
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    payload = {
        'key': config.TRELLO_KEY,
        'token': config.TRELLO_TOKEN,
        }
    items = ids_to_import(content_type)
    item_loop = []
    for item_id in items:
        # content
        content_url = "https://api.trello.com/1/cards/" + item_id
        content_r = requests.get(content_url, params=payload)
        content = content_r.json()
        date = content.get("due", "NA")
        dt = parse(date)
        image = None
        credits = None
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
            credits = get_credits(item_id)
            author = "Mary-Ann Horley"
        taxonomy = get_labels(item_id)
        info = {
                "date": dt,
                "item_id": item_id,
                "title": content.get("name", "NA"),
                "image": image,
                "text": content.get("desc", "NA"),
                "type": content_type,
                "credits": credits,
                "taxonomy": taxonomy,
                "author": author,
            }
        # add to db
        post_id = db.content.insert_one(info).inserted_id
        print(str(post_id) + " " + str(content_type))