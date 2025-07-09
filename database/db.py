from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client["webcrawler_db"]
unprocessed_collection = db["unprocessed_pages"]
indexed_collection = db["indexed_data"]
visited_collection = db["visited_urls"]

def save_page(url: str, html_content: str):
    try:
        unprocessed_collection.insert_one({
            "url": url,
            "html_content": html_content
        })
    except DuplicateKeyError:
        pass

def fetch_unprocessed():
    """
    Returns:
        list: A list of MongoDB documents (dicts) representing unprocessed pages.
    """
    try:
        return list(unprocessed_collection.find())
    except Exception as e:
        pass

def clear_processed_html_table():
    """
    This function is only to be used to clear the unprocessed_pages collection after indexing has completed
    """
    unprocessed_collection.delete_many({})

def save_indexed_data_to_collection(indexed_data):
    """
    Saves the indexed data (list of dicts) to the 'indexed_data' collection in the database.
    Each item in indexed_data should be a dict with at least 'word', 'url', and 'weight' keys.
    """
    if not indexed_data:
            return
    try:
        indexed_collection.insert_many(indexed_data)
    except Exception as e:
        pass

def is_url_visited(url: str) -> bool:
    """Check if a URL is already in the visited_urls collection."""
    return visited_collection.find_one({"url": url}) is not None

def mark_url_visited(url: str):
    """Add a URL to the visited_urls collection."""
    try:
        visited_collection.insert_one({"url": url})
    except DuplicateKeyError:
        pass