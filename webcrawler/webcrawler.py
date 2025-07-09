import threading
import time
from collections import deque
from crawler_logic import worker
from utils.logger import logger

# TODO: 

# - instead of storing the words separated, we can store the html content, then implement the indexer,
#   the indexer can be in charge of pulling the html, and then extracting the useful words and 
#   adding them into a map with frequency and weights ( find some algorithm like PageRank )
# - clean up the structure of the code; move things out into their own files or functions to separate concerns

# threading flag to signal workers to stop crawling
stop_crawling_flag = threading.Event()

# Constants
MAX_PAGES_TO_CRAWL = 500
CRAWL_DELAY_SECONDS = 0.2
NUMBER_OF_WORKERS = 20

# Shared data structures
visited_urls = set()
visited_urls_lock = threading.Lock()
url_queue = deque()  # Shared queue of URLs to crawl

def main():
    start_url = "https://en.wikipedia.org/wiki/Go_(programming_language)"
    logger.info(f"Starting Wikipedia crawler from: {start_url}")

    # begin the url queue with the starting url
    url_queue.append(start_url)

    # start threads
    threads = []
    for i in range(NUMBER_OF_WORKERS):
        thread = threading.Thread(
            target=worker,
            name=f"Worker-{i+1}",
            args=(url_queue, visited_urls, visited_urls_lock, stop_crawling_flag, MAX_PAGES_TO_CRAWL, CRAWL_DELAY_SECONDS)
        )
        threads.append(thread)
        thread.start()

    while not stop_crawling_flag.is_set() or any(thread.is_alive() for thread in threads):
        time.sleep(1)
        with visited_urls_lock:
            if len(visited_urls) >= MAX_PAGES_TO_CRAWL and not stop_crawling_flag.is_set():
                logger.info(f"Main: Max pages ({MAX_PAGES_TO_CRAWL}) reached. Signalling stop.")
                stop_crawling_flag.set()

    # waiting for all worker threads to finish
    for thread in threads:
        thread.join()

    print("\n--- Crawled Pages Complete ---")

if __name__ == "__main__":
    main()