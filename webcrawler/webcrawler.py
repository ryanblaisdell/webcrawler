import threading
import time
from collections import deque
from .crawler_logic import worker
from utils.logger import logger
from database.db import is_url_visited
from tqdm import tqdm

# TODO: 
# - clean up the structure of the code; move things out into their own files or functions to separate concerns
# - next up: implementing the query engine to pull relavent results from the DB

#region - Constants
MAX_PAGES_TO_CRAWL = 500
CRAWL_DELAY_SECONDS = 0.2
NUMBER_OF_WORKERS = 20
STOP_CRAWLING_FLAG = threading.Event()
#endregion

#region Shared data structures
visited_urls = set()
visited_urls_lock = threading.Lock()
url_queue = deque()  # Shared queue of URLs to crawl
#endregion

def main():
    start_url = "https://en.wikipedia.org/wiki/Association_football"

    if is_url_visited(start_url):
        logger.error(f"Starting URL has already been visited.\n\n URL:{start_url}")
        return

    logger.info(f"Starting Wikipedia crawler from: {start_url}\n")

    # begin the url queue with the starting url
    url_queue.append(start_url)

    # start threads
    threads = []
    for i in range(NUMBER_OF_WORKERS):
        thread = threading.Thread(
            target=worker,
            name=f"Worker-{i+1}",
            args=(url_queue, visited_urls, visited_urls_lock, STOP_CRAWLING_FLAG, MAX_PAGES_TO_CRAWL, CRAWL_DELAY_SECONDS)
        )
        threads.append(thread)
        thread.start()

    # begin crawling pages
    with tqdm(total=MAX_PAGES_TO_CRAWL, desc="Crawled pages") as pbar:
        last_count = 0

        while not STOP_CRAWLING_FLAG.is_set() or any(thread.is_alive() for thread in threads):
            time.sleep(1)
            with visited_urls_lock:

                # these variable are for the progress bar tracking
                current_count = len(visited_urls)
                pbar.update(current_count - last_count)
                last_count = current_count

                # signal that crawling should stop to all workers
                if current_count >= MAX_PAGES_TO_CRAWL and not STOP_CRAWLING_FLAG.is_set():
                    logger.info(f"\nMain: Max pages ({MAX_PAGES_TO_CRAWL}) reached. Signalling stop.")
                    STOP_CRAWLING_FLAG.set()

    for thread in threads:
        thread.join()

    print("\n--- Crawled Pages Complete ---")

if __name__ == "__main__":
    main()