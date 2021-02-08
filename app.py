from flask import Flask, render_template, request, url_for, redirect, flash
from flask_bootstrap import Bootstrap
from flask_basicauth import BasicAuth

import os 
import json
from datetime import datetime
import time

import requests
import mistune
from pymongo import MongoClient
import pymongo
from slugify import slugify 

import config
from taxonomy import add_existing_to_tax, get_tax_info, get_content_from_taxonomy
from forms import PostForm, TaxForm
from functions import add_to_db, create_item_id, get_content, add_to_tags, add_to_subjects, add_subject, add_tag

app = Flask(__name__)
app.config.from_pyfile('config.py', silent=True)

basic_auth = BasicAuth(app)

bootstrap = Bootstrap(app)

markdown = mistune.Markdown()



@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route("/")
def index():
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog
    
    content = list(db.content.find({}).sort([("date", -1), ("_id", 1)]).limit(30))
    
    return render_template("index.html", content=content)



@app.route("/admin")
@basic_auth.required
def admin():
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog
    # get all posts created within flask
    posts = list(db.content.find({
      "type": "post"
    }))
    tags = list(db.tags.find({
        "posts": {"$exists": True },
        "links": {"$exists": True },
    }))
    subjects = list(db.subjects.find({
        "posts": {"$exists": True },
        "links": {"$exists": True }, 
    }))
    return render_template("admin.html", posts=posts, tags=tags, subjects=subjects)


@app.route("/add_post", methods=('GET', 'POST'))
@basic_auth.required
def add_new_post():
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog
    form = PostForm()
    if form.validate_on_submit():
        # split tag string
        raw_tags = form.tags.data
        tags = raw_tags.split(", ")
        for tag in tags:
            slugify(tag)
            add_tag(tag, slugify(tag, separator='_'))
        # split subject string 
        raw_subjects = form.subjects.data
        subjects = raw_subjects.split(", ")
        for subject in subjects:
            slugify(subject)
            add_subject(subject, slugify(subject, separator='_'))
        # assemble data
        info = {
          "item_id": create_item_id(),
          "via": "flask",
          "date": datetime.now(),
          "type": "post",
          "title": form.title.data,
          "slug": slugify(form.title.data, separator='_'),
          "author": form.author.data,
          "intro": form.intro.data,
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
        print(add_to_tags(post_id))
        print(add_to_subjects(post_id))
        # add flashed message
        flash('Post added successfully')
        return render_template("add_post.html", form=form)
    return render_template("add_post.html", form=form)


@app.route("/delete/post/<item_id>")
@basic_auth.required
def delete_post(item_id):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog
    db.content.delete_one({"item_id": item_id})
    # flashed message
    flash('Post deleted successfully')
    return redirect("/admin")


@app.route("/edit/tag/<slug>", methods=('GET', 'POST'))
@basic_auth.required
def edit_tag(slug):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog
    # get existing tag details
    content = db.tags.find_one({
        "slug": slug,
    })
    form = TaxForm(data=content)
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        image = form.image.data
        image_creator = form.image_creator.data
        image_creator_url = form.image_creator_url.data
        info = {
            "updated": {
                "via": "flask",
                "date": datetime.now(),
              },
            "name": name,
            "description": description,
            "image": image,
            "credits": {
                "name": form.image_creator.data,
                "url": form.image_creator_url.data,
                }
              }
        db.tags.update_one({"slug": slug}, {"$set": info})
        flash('Tag edited successfully')
        return render_template("edit_tag.html", form=form)
    return render_template("edit_tag.html", form=form)

@app.route("/edit/subject/<slug>", methods=('GET', 'POST'))
@basic_auth.required
def edit_subject(slug):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog
    # get existing values
    content = db.subjects.find_one({
        "slug": slug,
    })
    # get form
    form = TaxForm(data=content)
    # process form data
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        image = form.image.data
        image_creator = form.image_creator.data 
        image_creator_url = form.image_creator_url.data
        info = {
          "updated": {
            "via": "flask",
            "date": datetime.now(),
          },
          "name": name,
          "description": description,
          "image": image,
          "credits": {
            "name": image_creator,
            "url": image_creator_url,
          }
        }
    # update db
        db.subjects.update_one({"slug": slug}, {"$set": info})
    # flash message
        flash('Subject edited successfully')
        return render_template("edit_subject.html", form=form)
    return render_template("edit_subject.html", form=form)


@app.route("/edit/post/<item_id>", methods=('GET', 'POST'))
@basic_auth.required
def edit_post(item_id):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog
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
          "intro": form.intro.data,
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
        add_to_tax(item_id)
        # add flashed message
        flash('Post edited successfully')
        return render_template("edit_post.html", form=form)
    return render_template("edit_post.html", form=form, item_id=item_id)


@app.route("/subjects")
def subjects():
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog
    subjects = list(db.subjects.find({ 
      "posts": {"$exists": True }, 
      "links": {"$exists": True } 
      }))
    return render_template("subjects.html", subjects=subjects)


@app.route("/tags")
def tags():
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog
    tags = list(db.tags.find({ 
      "posts": {"$exists": True }, 
      "links": {"$exists": True } 
      }))
    return render_template("tags.html", tags=tags)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/cron")
def cron():
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog
    start = time.time()
    add_to_db("post")
    add_to_db("link")
    add_to_db("download")
    add_to_db("page")
    end = time.time()
    time_taken = end - start
    return render_template("cron.html", time_taken=time_taken)


@app.route("/tag/<tag>")
def tag(tag):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog

    # get tag into including header image
    info = db.tags.find_one({ "slug": tag })

    content = get_content_from_taxonomy("tags", tag)
    
    return render_template("taxonomy.html", info=info, content=content)


@app.route("/subject/<subject>")
def subject(subject):

    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog

    info = db.subjects.find_one({ "slug": subject })

    content = get_content_from_taxonomy("subjects", subject)

    return render_template("taxonomy.html", content=content, info=info)


@app.route("/post/<post_id>")
def post(post_id):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog
    info = db.content.find_one({"item_id": post_id})
    text = markdown(info["text"])
    tags = []
    for tag in info["tags"]:
        if tag != None:
            tag_info = db.tags.find_one({
                "name": tag
            })
            tags.append(tag_info)
    subjects = []
    for subject in info["subjects"]:
        if subject != None:
            subject_info = db.subjects.find_one({
                "name": subject
            })
            subjects.append(subject_info)
    return render_template("post.html", info=info, text=text, tags=tags, subjects=subjects)


@app.route("/page/<page_id>")
def page(page_id):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog
    info = db.content.find_one({"item_id": page_id})
    text = markdown(info["text"])
    return render_template("page.html", info=info, text=text)


@app.route("/download/<page_id>")
def download(page_id):
    db = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority&?ssl=true&ssl_cert_reqs=CERT_NONE", connect=False).blog
    info = db.content.find_one({"item_id": page_id})
    text = markdown(info["text"])
    tags = []
    for tag in info["tags"]:
        if tag != None:
            tag_info = db.tags.find_one({
                "name": tag
            })
            tags.append(tag_info)
    subjects = []
    for subject in info["subjects"]:
        if subject != None:
            subject_info = db.subjects.find_one({
                "name": subject
            })
            subjects.append(subject_info)
    return render_template("download.html", info=info, text=text, tags=tags, subjects=subjects)


# if __name__ == '__main__':
    # app.run(debug=True, host='0.0.0.0')