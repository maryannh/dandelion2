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
    name = tax.get("name", "No name")
    description = tax.get("description", "No description")
    image = tax.get("image", "No image")
    credits = tax.get("credits")
    image_creator = credits.get("name", "No creator name")
    image_creator_url = credits.get("url", "No creator URL")
    info = {
      "name": name,
      "description": description,
      "image": image,
      "image_creator": image_creator,
      "image_creator_url": image_creator_url,
    }
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

        term_content = []

        if content_ids["posts"]:
            posts = []
            for post in content_ids["posts"]:
                content = db.content.find_one({ "_id": post })
                intro = content["text"][:120]
                if content["intro"]:
                    intro = content["intro"]
                info = {
                    "title": content["title"],
                    "slug": content["slug"],
                    "item_id": content["item_id"],
                    "date": content["date"],
                    "intro": intro,
                    "image": content["image"]
                }
                posts.append(info)
            tag_content.append(posts)

        if content_ids["links"]:
            links = []
            for link in content_ids["links"]:
                content = db.content.find_one({ "_id": link })
                info = {
                    "title": content["title"],
                    "slug": content["slug"],
                    "item_id": content["item_id"],
                    "date": content["date"],
                    "url": content["text"],
                }
                links.append(info)
            tag_content.append(links)
        
        if content_ids["downloads"]:
            downloads = []
            for download in content_ids["downloads"]:
                content = db.content.find_one({ "_id": download })
                intro = content["text"][:120]
                if content["intro"]:
                    intro = content["intro"]
                info = {
                    "title": content["title"],
                    "slug": content["slug"],
                    "item_id": content["item_id"],
                    "date": content["date"],
                    "intro": intro,
                }
                downloads.append(info)
            term_content.append(downloads)

        return term_content