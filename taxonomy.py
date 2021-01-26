from pymongo import MongoClient
import dns
from bson.objectid import ObjectId
from functions import add_to_tax

def add_existing_to_tax():
  db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
  posts = list(db.content.find({"type": "post"}))
  for post in posts:
    for tag in post["tags"]:
      db.tags.update_one(
        {"slug": tag}, 
        {"$addToSet": {"posts": post["_id"]}}
        )
    for subject in post["subjects"]:
      db.subjects.update_one(
        {"slug": subject}, 
        {"$addToSet": {"posts": post["_id"]}}
      )
  links = list(db.content.find({"type": "link"}))
  for link in links:
    for tag in link["tags"]:
      db.tags.update_one(
        {"slug": tag}, 
        {"$addToSet": {"links": link["_id"]}}
        )
    for subject in link["subjects"]:
      db.subjects.update_one(
        {"slug": subject}, 
        {"$addToSet": {"links": link["_id"]}}
      )
  downloads = list(db.content.find({"type": "download"}))
  for download in downloads:
    for tag in download["tags"]:
      db.tags.update_one(
        {"slug": tag}, 
        {"$addToSet": {"downloads": download["_id"]}}
        )
    for subject in download["subjects"]:
      db.subjects.update_one(
        {"slug": subject}, 
        {"$addToSet": {"downloads": download["_id"]}}
      )

