from flask import Flask, render_template, request, url_for, redirect, flash
from flask_bootstrap import Bootstrap
from flask_basicauth import BasicAuth

import os 
import json
from datetime import datetime

import requests
import mistune
from pymongo import MongoClient
import pymongo
from slugify import slugify 

import config
from functions import add_to_db, create_item_id, get_content
from forms import PostForm

app = Flask(__name__)
app.config.from_pyfile('config.py', silent=True)

basic_auth = BasicAuth(app)

bootstrap = Bootstrap(app)

markdown = mistune.Markdown()

def get_subjects():
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    subject_list = list(db.subjects.find())
    subjects = []
    for subject in subject_list:
        slug = subject["slug"]
        name = subject["name"]
        count = db.content.count({
        "subjects": slug
            })
        if int(count) > 2:
            info = {
              "slug": slug,
              "name": name,
              "count": count,
            }
        subjects.append(info)
    return subjects

def get_tags():
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    tag_list = list(db.tags.find())

    tags = []
    
    for tag in tag_list:
        slug = tag["slug"]
        name = tag["name"]
        count = db.content.count({
          "tags": slug
          })
        if int(count) > 2:
          info = {
            "slug": slug,
            "name": name,
            "count": count,
          }
          tags.append(info)
    return tags

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/")
def index():
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    post_loop = list(db.content.find({
        "type": "post"
    }).sort({
      "date": -1, 
      "_id": 1,
      }).limit(10))
    page_loop = list(db.content.find({
        "type": "page"
    }))
    download_loop = list(db.content.find({
        "type": "download"
    }).sort({
      "date": -1, 
      "_id": 1,
      }).limit(10))
    link_loop = list(db.content.find({
        "type": "link"
    }).sort({
      "date": -1, 
      "_id": 1,
      }).limit(10))
    subjects = get_subjects()[:10]
    tags = get_tags()[:10]
    return render_template("index.html", post_loop=post_loop, page_loop=page_loop,
        download_loop=download_loop, link_loop=link_loop, subjects=subjects, tags=tags)

@app.route("/admin")
@basic_auth.required
def admin():
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    # get all posts created within flask
    posts = list(db.content.find({
      "type": "post"
    }))
    return render_template("admin.html", posts=posts)

@app.route("/add_post", methods=('GET', 'POST'))
@basic_auth.required
def add_new_post():
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    form = PostForm()
    if form.validate_on_submit():
        # split tag string
        raw_tags = form.tags.data
        tags = raw_tags.split(", ")
        # split subject string 
        raw_subjects = form.subjects.data
        subjects = raw_subjects.split(", ")
        # assemble data
        info = {
          "item_id": create_item_id(),
          "via": "flask",
          "date": datetime.now(),
          "type": "post",
          "title": form.title.data,
          "slug": slugify(form.title.data, separator='_'),
          "author": form.author.data,
          "text": form.text.data,
          "image": form.image.data,
          "tags": tags,
          "subjects": subjects,
          "credits": {
            "name": form.image_creator.data,
            "url": form.image_creator_url.data,
          }
        }
        # add data to db
        post_id = db.content.insert_one(info).inserted_id
        # add flashed message
        flash('Post added successfully')
        return render_template("add_post.html", form=form)
    return render_template("add_post.html", form=form)

@app.route("/delete/post/<item_id>")
@basic_auth.required
def delete_post(item_id):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    db.content.delete_one({"item_id": item_id})
    # flashed message
    flash('Post deleted successfully')
    return redirect("/admin")

@app.route("/edit/post/<item_id>", methods=('GET', 'POST'))
@basic_auth.required
def edit_post(item_id):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    # get existing values
    content = get_content(item_id)
    form = PostForm(data=content)
    # add form submission
    if form.validate_on_submit():
        # split tag string
        raw_tags = form.tags.data
        tags = raw_tags.split(", ")
        # split subject string 
        raw_subjects = form.subjects.data
        subjects = raw_subjects.split(", ")
        # assemble data
        info = {
          "updated": {
            "via": "flask",
            "date": datetime.now(),
          },
          "type": "post",
          "title": form.title.data,
          "slug": slugify(form.title.data, separator='_'),
          "author": form.author.data,
          "text": form.text.data,
          "image": form.image.data,
          "tags": tags,
          "subjects": subjects,
          "credits": {
            "name": form.image_creator.data,
            "url": form.image_creator_url.data,
          }
        }
        # add data to db
        db.content.update_one({"item_id": item_id}, {"$set": info})
        # add flashed message
        flash('Post edited successfully')
        return render_template("edit_post.html", form=form)
    return render_template("edit_post.html", form=form, item_id=item_id)

@app.route("/subjects")
def subjects():
    subjects = get_subjects()
    return render_template("subjects.html", subjects=subjects)

@app.route("/tags")
def tags():
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog

    tags = get_tags()

    return render_template("tags.html", tags=tags)

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

    return render_template("subject.html", links=links, posts=posts, tag=tag, downloads=downloads, info=info)

@app.route("/post/<post_id>")
def post(post_id):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    info = db.content.find_one({"item_id": post_id})
    text = markdown(info["text"])
    return render_template("post.html", info=info, text=text)

@app.route("/page/<page_id>")
def page(page_id):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    info = db.content.find_one({"item_id": page_id})
    text = markdown(info["text"])
    return render_template("page.html", info=info, text=text)

@app.route("/download/<page_id>")
def download(page_id):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False).blog
    info = db.content.find_one({"item_id": page_id})
    text = markdown(info["text"])
    return render_template("page.html", info=info, text=text)

# if __name__ == '__main__':
    # app.run(debug=True, host='0.0.0.0')