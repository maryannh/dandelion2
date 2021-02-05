from pymongo import MongoClient
import dns
from bson.objectid import ObjectId
import config
import os

def get_tax_info(slug, tax_type):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog
    if tax_type == "tag":
        tax = db.tag.find_one({
          "slug": slug,
        })
    elif tax_type == "subject":
        tax = db.subject.find_one({
          "slug": slug,
        })
        print(tax)
    info = {
      "name": tax["name"],
      "description": tax["description"],
      "image": tax["image"],
      "image_creator": tax["credits"]["name"],
      "image_creator_url": tax["credits"]["url"],
    }
    print(info)
    return info


def add_existing_to_tax():
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog
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

            
def get_content_from_taxonomy(taxonomy, term):
        db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog

        if taxonomy == "tags":
            conn = db.tags
        elif taxonomy == "subjects":
            conn = db.subjects

        content_ids = conn.find_one({ "slug": term }, { "posts": 1, "links": 1, "downloads": 1, "_id": 0 })
        
        posts = []
        if content_ids.get("posts") != None:
            posts = content_ids.get("posts")
        
        links = []
        if content_ids.get("links") != None:
            links = content_ids.get("links")
        
        downloads = []
        if content_ids.get("downloads") != None:
            downloads = content_ids.get("downloads")
        
        ids = posts + links + downloads
        
        ids.sort(reverse=True)
        
        if len(ids) > 1:
            content = []
            for item in ids[:30]:
                content_info = db.content.find_one({ "_id": item })
                intro = content_info["text"]
                if content_info.get("intro") == None:
                    intro = content_info.get("intro")
                info = {
                    "title": content_info.get("title", "NA"),
                    "slug": content_info.get("slug", "NA"),
                    "intro": intro,
                    "text": content_info.get("text", "NA"),
                    "image": content_info.get("image", "NA"),
                    "author": content_info.get("author", "NA"),
                    "type": content_info.get("type", "NA"),
                    "date": content_info.get("date", "NA"),
                }
                content.append(info)
        else:
            content = ["Sorry, no content available"]
            
        return content
    
def get_item_tags(item_id):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog
    raw_tags = db.content.find_one({"item_id": item_id}, {"tags": 1, "_id": 0})
    tags = []
    for tag in raw_tags:
        tag_info = db.tags.find_one({"name": tag})
        info = {
        "name": tag,
        "slug": tag_info["slug"]
        }
        tags.append(info)
    return tags

    
def get_item_subjects(item_id):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog
    raw_subjects = db.content.find_one({"item_id": item_id}, {"tags": 1, "_id": 0})
    subjects = []
    for subject in raw_subjects:
        subject_info = db.tags.find_one({"name": subject})
        info = {
        "name": subject,
        "slug": subject_info["slug"]
        }
        subjects.append(info)
    return subjects
