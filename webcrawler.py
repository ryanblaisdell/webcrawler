import logging
import threading
import time
from collections import deque
from crawler_logic import worker

# TODO: add the db connection into the crawling to being storing this crawled data

# configure logging for crawler application
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# threading flag to signal workers to stop crawling
stop_crawling_flag = threading.Event()

# Constants
MAX_PAGES_TO_CRAWL = 10
CRAWL_DELAY_SECONDS = 0.5
NUMBER_OF_WORKERS = 5

# Shared data structures
visited_urls = set()
visited_urls_lock = threading.Lock()
url_queue = deque()  # Shared queue of URLs to crawl
crawled_html_content = {}  # Stores the HTML content of crawled pages, keyed by URL
crawled_html_content_lock = threading.Lock()  # Ensures only one thread modifies crawled_content at a time


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
            args=(url_queue, visited_urls, visited_urls_lock, crawled_html_content, crawled_html_content_lock, stop_crawling_flag, MAX_PAGES_TO_CRAWL, CRAWL_DELAY_SECONDS)
        )
        threads.append(thread)
        thread.start()

    while not stop_crawling_flag.is_set() or any(thread.is_alive() for thread in threads):
        time.sleep(1)
        with visited_urls_lock:
            if len(visited_urls) >= MAX_PAGES_TO_CRAWL and not stop_crawling_flag.is_set():
                logger.info(f"Main: Max pages ({MAX_PAGES_TO_CRAWL}) reached. Signalling stop.")
                stop_crawling_flag.set()

    # Wait for all worker threads to finish
    for thread in threads:
        thread.join()

    logger.info(f"Crawling finished. {len(crawled_html_content)} pages crawled.")

    # Optionally, print a summary
    print("\n--- Crawled Pages Complete ---")
    sorted_urls = sorted(crawled_html_content.keys())
    for url in sorted_urls:
        html_content, page_content = crawled_html_content[url]
        print(f"URL: {url}\nHTML Content Length: {len(html_content)}\nPage Content Length: {len(page_content)}\n")

if __name__ == "__main__":
    main()