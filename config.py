import os

TRELLO_KEY = os.environ.get("TRELLO_KEY")
TRELLO_TOKEN = os.environ.get("TRELLO_TOKEN")
BOARD_ID = os.environ.get("BOARD_ID")
POSTS_LABEL = os.environ.get("POSTS_LABEL")
PAGES_LABEL = os.environ.get("PAGES_LABEL")
DOWNLOADS_LABEL = os.environ.get("DOWNLOADS_LABEL")
LINKS_LABEL = os.environ.get("LINKS_LABEL")
BASE_URL = os.environ.get("BASE_URL")
MONGODB_USER = os.environ.get("MONGODB_USER")
MONGODB_PASS = os.environ.get("MONGODB_PASS")
SECRET_KEY = os.environ.get("SECRET_KEY")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)