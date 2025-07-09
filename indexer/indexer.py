from database.db import fetch_unprocessed, save_indexed_data_to_collection
from indexer.indexer_logic import process_batch_with_tfidf
from utils.logger import logger

def index_raw_html_pages():
    html_batch = fetch_unprocessed()

    if not html_batch:
        print("There is no html content to process...")
        return

    indexed_data = process_batch_with_tfidf(html_batch)
    logger.info("Indexing of unprocessed data has completed.")

    # add this line back when you want to remove the entries in the collections
    # clear_processed_html_table()
    logger.info("Cleared unprocessed pages collection on database.")

    save_indexed_data_to_collection(indexed_data)
    logger.info("Indexing is complete...")

    return indexed_data

if __name__ == "__main__":
       index_raw_html_pages()