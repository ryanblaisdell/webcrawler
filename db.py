from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client["webcrawler_db"]
collection = db["pages"]
collection.create_index("url", unique=True)

def save_page(url, html_content, page_content):
    try:
        collection.insert_one({
            "url": url,
            "html_content": html_content,
            "page_content": page_content
        })
    except DuplicateKeyError:
        pass