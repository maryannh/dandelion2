from flask import Flask, render_template, request, url_for, redirect
import requests
import mistune
import config
from pymongo import MongoClient
import pymongo
import datetime
import os 
import json
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
# from dateutil import parser
from functions import add_to_db
from db import init_db_command
from user import User

app = Flask(__name__)
app.config.from_pyfile('config.py', silent=True)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# Naive database setup
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


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
    subjects = get_subjects()[:10]
    tags = get_tags()[:10]
    return render_template("index.html", post_loop=post_loop, page_loop=page_loop,
        download_loop=download_loop, link_loop=link_loop, subjects=subjects, tags=tags)

@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    # Find out what URL to hit to get tokens that allow you to ask for things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
      token_endpoint,
      authorization_response=request.url,
      redirect_url=request.base_url,
      code=code
    )
    token_response = requests.post(
      token_url,
      headers=headers,
      data=body,
      auth=(config.GOOGLE_CLIENT_ID, config.GOOGLE_CLIENT_SECRET),
    )
    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))
    # Now that you have tokens (yay) let's find and hit the URL from Google that gives you the user's profile information, including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400
    # Create a user in your db with the information provided by Google
    user = User(
      id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )
    # Doesn't exist? Add it to the database.
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)
    # Begin user session by logging the user in
    login_user(user)
    # Send user back to homepage
    return redirect(url_for("admin"))

@app.route("/admin")
@login_required
def admin():
    return "logged in!"

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

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