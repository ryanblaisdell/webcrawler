from database.db import fetch_unprocessed, save_indexed_data_to_collection, clear_processed_html_table
from indexer.indexer_logic import process_batch_with_tfidf
from utils.logger import logger
from tqdm import tqdm

def index_raw_html_pages():
    with tqdm(total=1, desc="Fetching unprocessed pages", bar_format="{l_bar}{bar} [time elapsed: {elapsed}]") as pbar:
        html_batch = fetch_unprocessed()
        pbar.update(1)
        
    if not html_batch:
        return

    indexed_data = process_batch_with_tfidf(html_batch)

    with tqdm(total=1, desc="Clearing unprocessed collection", bar_format="{l_bar}{bar} [time elapsed: {elapsed}]") as pbar:
        clear_processed_html_table()
        pbar.update(1)

    with tqdm(total=1, desc="Saving indexeded data to the database", bar_format="{l_bar}{bar} [time elapsed: {elapsed}]") as pbar:
        save_indexed_data_to_collection(indexed_data)
        pbar.update(1)

    logger.info("Indexed has completed.")
    
    return indexed_data

if __name__ == "__main__":
       index_raw_html_pages()