from flask import Flask, render_template
import requests
import mistune
import config
from pymongo import MongoClient
import pymongo
import datetime
from functions import add_to_db

app = Flask(__name__)

app.config.from_pyfile('config.py', silent=True)

client = MongoClient("mongodb+srv://admin:" + config.MONGODB_PASS + "@cluster0.mfakh.mongodb.net/blog?retryWrites=true&w=majority", connect=False)
db = client.blog

markdown = mistune.Markdown()

@app.route("/")
def index():
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
    return render_template("index.html", post_loop=post_loop, page_loop=page_loop,
        download_loop=download_loop, link_loop=link_loop)

@app.route("/cron")
def cron():
    add_to_db("post")
    add_to_db("link")
    add_to_db("download")
    add_to_db("page")
    return render_template("cron.html")

@app.route("/post/<post_id>")
def post(post_id):
    info = db.content.find_one({"item_id": post_id})
    text = markdown(info["text"])
    dt = parse(info["date"])
    date = dt.date().strftime("%-d %B %Y")
    return render_template("post.html", info=info, text=text, date=date)

@app.route("/page/<page_id>")
def page(page_id):
    info = db.content.find_one({"item_id": page_id})
    text = markdown(info["text"])
    return render_template("page.html", info=info, text=text)

@app.route("/download/<page_id>")
def download(page_id):
    info = db.content.find_one({"item_id": page_id})
    text = markdown(info["text"])
    return render_template("page.html", info=info, text=text)

# if __name__ == '__main__':
   # app.run(debug=True, host='0.0.0.0')
