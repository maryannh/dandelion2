from flask import Flask, render_template, request
import requests
import mistune
import config
from pymongo import MongoClient
import pymongo
import datetime
import os 
# from dateutil import parser
from functions import add_to_db

app = Flask(__name__)

app.config.from_pyfile('config.py', silent=True)

markdown = mistune.Markdown()

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/")
def index():
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    post_loop = list(db.content.find({
        "type": "post"
    }).sort("date", -1))
    page_loop = list(db.content.find({
        "type": "page"
    }))
    download_loop = list(db.content.find({
        "type": "download"
    }).sort("date", -1))
    link_loop = list(db.content.find({
        "type": "link"
    }).sort("date", -1))
    db.stats.insert_one({
      "datetime": datetime.datetime.now(),
      "page": "index",
      "type": "index",
      "referrer": request.referrer,
    })
    return render_template("index.html", post_loop=post_loop, page_loop=page_loop,
        download_loop=download_loop, link_loop=link_loop)

@app.route("/about")
def about():
  return render_template("about.html")

@app.route("/cron")
def cron():
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    add_to_db("post")
    add_to_db("link")
    add_to_db("download")
    add_to_db("page")
    return render_template("cron.html")

@app.route("/stats")
def stats():
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    return render_template("stats.html")

@app.route("/why")
def why():
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    posts = list(db.content.find({
        "type": "post",
        "tags": {"$in": ["why_and_how"] }
    }).sort("date", -1))
    links = list(db.content.find({
        "type": "link",
        "tags": {"$in": ["why_and_how"] }
    }).sort("date", -1))
    db.stats.insert_one({
      "datetime": datetime.datetime.now(),
      "page": "why_and_how",
      "type": "tag",
      "referrer": request.referrer,
    })
    return render_template("why.html", links=links, posts=posts)

@app.route("/tag/<tag>")
def tag(tag):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    posts = list(db.content.find({
        "type": "post",
        "tags": {"$in": [tag] }
    }).sort("date", -1))
    links = list(db.content.find({
        "type": "link",
        "tags": {"$in": [tag] }
    }).sort("date", -1))
    downloads = list(db.content.find({
        "type": "download",
        "tags": {"$in": [tag] }
    }).sort("date", -1))
    info = db.tags.find_one({
        "slug": tag,
    })
    db.stats.insert_one({
      "datetime": datetime.datetime.now(),
      "page": "tag",
      "type": "tag",
      "referrer": request.referrer,
    })
    return render_template("tag.html", links=links, posts=posts, tag=tag, downloads=downloads, info=info)

@app.route("/subject/<subject>")
def subject(subject):
  
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog

    posts_query = db.content.find({
        "type": "post",
        "subjects": {"$in": [subject] }
    }).sort("date", -1)
    posts = None
    if posts_query != None:
        posts = list(posts_query)
    # if there's no posts, this needs to return none

    links_query = db.content.find({
        "type": "link",
        "subjects": {"$in": [subject] }
    }).sort("date", -1)
    links = None
    if links_query != None:
        links = list(links_query)

    downloads_query = db.content.find({
        "type": "download",
        "subjects": {"$in": [subject] }
    }).sort("date", -1)
    downloads = None
    if downloads_query != None:
        downloads = list(downloads_query)

    info = db.subjects.find_one({
        "slug": subject,
    })

    db.stats.insert_one({
      "datetime": datetime.datetime.now(),
      "page": "tag",
      "type": "tag",
      "referrer": request.referrer,
    })

    return render_template("subject.html", links=links, posts=posts, tag=tag, downloads=downloads, info=info)

@app.route("/post/<post_id>")
def post(post_id):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    info = db.content.find_one({"item_id": post_id})
    text = markdown(info["text"])
    db.stats.insert_one({
      "datetime": datetime.datetime.now(),
      "page": info["title"],
      "type": info["type"],
      "item_id": info["item_id"],
      "published": info["date"] ,   
      "tags": info["tags"],
      "subjects": info["subjects"],
      "referrer": request.referrer
    })
    return render_template("post.html", info=info, text=text)

@app.route("/page/<page_id>")
def page(page_id):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    info = db.content.find_one({"item_id": page_id})
    text = markdown(info["text"])
    db.stats.insert_one({
      "datetime": datetime.datetime.now(),
      "page": info["title"],
      "type": info["type"],
      "item_id": info["item_id"],
      "published": info["date"] ,
      "tags": info["tags"],
      "subjects": info["subjects"],
      "referrer": request.referrer    
      })
    return render_template("page.html", info=info, text=text)

@app.route("/download/<page_id>")
def download(page_id):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    info = db.content.find_one({"item_id": page_id})
    text = markdown(info["text"])
    db.stats.insert_one({
      "datetime": datetime.datetime.now(),
      "page": info["title"],
      "type": info["type"],
      "item_id": info["item_id"],
      "published": info["date"] ,
      "tags": info["tags"],
      "subjects": info["subjects"],
      "referrer": request.referrer
    })
    return render_template("page.html", info=info, text=text)

# if __name__ == '__main__':
    # app.run(debug=True, host='0.0.0.0')