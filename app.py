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

def content_stats(page_type, item_id, info):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    db.stats.insert_one({
      "datetime": datetime.datetime.now(),
      "page": info["title"],
      "type": page_type,
      "item_id": item_id,
      "published": info["date"],   
      "tags": info["tags"],
      "subjects": info["subjects"],
      "referrer": request.headers.get("Referer"),
      "string": request.user_agent.string,
    })

def cat_stats(page_type, page_name):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    db.stats.insert_one({
      "datetime": datetime.datetime.now(),
      "page": page_name,
      "type": page_type,
      "referrer": request.headers.get("Referer"),
      "string": request.user_agent.string,
    })

@app.errorhandler(404)
def page_not_found(e):
    cat_stats("error", "404")
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

    cat_stats("index", "index")

    return render_template("index.html", post_loop=post_loop, page_loop=page_loop,
        download_loop=download_loop, link_loop=link_loop)

@app.route("/subjects")
def subjects():
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog

    subject_list = list(db.subjects.find())
    print(subject_list)

    subjects = []
    
    for subject in subject_list:
        slug = subject["slug"]
        name = subject["name"]
        count = db.content.count({
          "subject": slug
          })
        # if int(count) > 2:
        info = {
            "slug": slug,
            "name": name,
            "count": count,
        }
        subjects.append(info)
    print(subjects)
    cat_stats("index", "subjects")

    return render_template("subjects.html", subjects=subjects)

@app.route("/tags")
def tags():
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog

    tags_list = list(db.tags.find())

    tag_count = []
    
    for tag in tag_list:
        slug = tag["slug"]
        name = tag["name"]
        count = db.content.count({
          "tag": slug
          })
        
        if count > 2:
          info = {
            "slug": slug,
            "name": name,
            "count": count,
          }
          tag_count.append(info)

    cat_stats("index", "tags")

    return render_template("tags.html", tag_count=tag_count)

@app.route("/about")
def about():
    cat_stats("page", "about")
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
    cat_stats("tag", "why_and_how")
    return render_template("why.html", links=links, posts=posts)

@app.route("/tag/<tag>")
def tag(tag):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog

    posts_query = db.content.find({
        "type": "post",
        "tags": {"$in": [tag] }
    }).sort("date", -1)
    posts = None
    if posts_query != None:
        posts = list(posts_query)

    links_query = db.content.find({
        "type": "link",
        "tags": {"$in": [tag] }
    }).sort("date", -1)
    links = None
    if links_query != None:
        links = list(links_query)

    downloads_query = db.content.find({
        "type": "download",
        "tags": {"$in": [tag] }
    }).sort("date", -1)
    downloads = None
    if downloads_query != None:
        downloads = list(downloads_query)

    info = db.tags.find_one({
        "slug": tag,
    })

    cat_stats("tag", tag)

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

    cat_stats("subject", subject)

    return render_template("subject.html", links=links, posts=posts, tag=tag, downloads=downloads, info=info)

@app.route("/post/<post_id>")
def post(post_id):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    info = db.content.find_one({"item_id": post_id})
    text = markdown(info["text"])
    content_stats("post", post_id, info)
    return render_template("post.html", info=info, text=text)

@app.route("/page/<page_id>")
def page(page_id):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    info = db.content.find_one({"item_id": page_id})
    text = markdown(info["text"])
    content_stats("page", page_id, info)
    return render_template("page.html", info=info, text=text)

@app.route("/download/<page_id>")
def download(page_id):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    info = db.content.find_one({"item_id": page_id})
    text = markdown(info["text"])
    content_stats("download", page_id, info)
    return render_template("page.html", info=info, text=text)

# if __name__ == '__main__':
    # app.run(debug=True, host='0.0.0.0')