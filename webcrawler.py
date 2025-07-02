#region - Imports
import requests
from bs4 import BeautifulSoup
from collections import deque
import threading
import time
import re
from urllib.parse import urljoin, urlparse
import logging
from bs4.element import Tag
#endregion

#region - main

# configure logging for crawler application
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# threading flag to signal workers to stop crawling
stop_crawling_flag = threading.Event()

def main():
    start_url = "https://en.wikipedia.org/wiki/Go_(programming_language)"
    logger.info(f"Starting Wikipedia crawler from: {start_url}")

    # begin the url queue with the starting url
    url_queue.append(start_url)

    # start threads
    num_workers = 5
    threads = []
    for i in range(num_workers):
        thread = threading.Thread(target=worker, name=f"Worker-{i+1}")
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

    # writing the crawled content out to a .txt file for now
    print("\n--- Crawled Content Summary ---")
    sorted_urls = sorted(crawled_html_content.keys())
    for url in sorted_urls:
        content = crawled_html_content[url]

        with open("crawled_html_content.txt", "a", encoding="utf-8") as f:
            f.write(f"URL: {url}\nContent:\n{content}\n\n")

#endregion

#region - Constants
MAX_PAGES_TO_CRAWL = 100
CRAWL_DELAY = 0.5  # seconds
USER_AGENT = "MyPythonWikipediaCrawler (contact@example.com)"
WIKIPEDIA_BASE_URL = "https://en.wikipedia.org"
#endregion

#region - Shared data structures

"""
visited_urls: A set of strings storing URLs that have already been visited.
Prevents the crawler from visiting the same URL multiple times.

visited_urls_lock: A threading.Lock object ensuring that only one thread
can access or modify the visited_urls set at a time. This prevents race
conditions and ensures thread safety when multiple threads are crawling
and updating the set of visited URLs.

url_queue: A deque of URLs to crawl.

crawled_html_content: A dictionary storing the HTML content of crawled pages, keyed by URL.

crawled_html_content_lock: A threading.Lock object ensuring that only one thread modifies crawled_html_content at a time.
"""
visited_urls = set()
visited_urls_lock = threading.Lock()
url_queue = deque()  # Shared queue of URLs to crawl; access may need to be synchronized if used by multiple threads
crawled_html_content = {}  # Stores the HTML content of crawled pages, keyed by URL
crawled_html_content_lock = threading.Lock()  # Ensures only one thread modifies crawled_content at a time
#endregion

#region - Helper functions
def fetch_and_parse(page_url: str) -> tuple[str, list]:
    """
    Fetches the HTML content of a URL and extracts all internal Wikipedia links.
    """
    headers = {"User-Agent": USER_AGENT}
    html_content = ""
    links = []

    try:
        response = requests.get(page_url, headers=headers, timeout=10)
        response.raise_for_status() # raise exceptions for bad http status codes ( 400s or 500s )
        html_content = response.text

        links = extract_wikipedia_links(html_content, page_url)

    except requests.exceptions.RequestException as e:
        logger.warning(f"Error fetching {page_url}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred with {page_url}: {e}")

    return html_content, links

def extract_wikipedia_links(html_content: str, base_url: str) -> list:
    """
    Parses HTML to find internal Wikipedia links using BeautifulSoup.
    Only returns English Wikipedia article links.
    """
    found_links = []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    for link_tag in soup.find_all('a', href=True):
        if not isinstance(link_tag, Tag):
            continue
        raw_link = link_tag.get('href')
        if not isinstance(raw_link, str):
            continue

        # ensure that the found url within the page will be joined with the base URl to form a valid URL
        resolved_url = urljoin(base_url, raw_link)

        # parse the parts of the URL so we can validate the URL and its content
        parsed_resolved_url = urlparse(resolved_url)

        # filter the links for only those in EN and main pages ( not second pages or subsections )
        if parsed_resolved_url.hostname == "en.wikipedia.org" and parsed_resolved_url.path.startswith("/wiki/") and ":" not in parsed_resolved_url.path and "#" not in parsed_resolved_url.fragment:
            found_links.append(resolved_url)
    
    return found_links

def worker():
    """
    Worker function to fetch and process URLs from the queue.
    """
    current_thread = threading.current_thread().name
    logger.info(f"{current_thread} starting.")

    while not stop_crawling_flag.is_set():
        page_url = None
        try:
            with visited_urls_lock:
                if len(url_queue) > 0: 
                    page_url = url_queue.popleft() 
                else:
                    time.sleep(0.1)
                    continue
        except IndexError:
            time.sleep(0.1)
            continue

        with visited_urls_lock:
            if page_url in visited_urls:
                continue

            visited_urls.add(page_url)
            current_pages_crawled = len(visited_urls)

            if current_pages_crawled >= MAX_PAGES_TO_CRAWL:
                logger.info(f"{current_thread}: Max pages ({MAX_PAGES_TO_CRAWL}) reached. Signalling stop.")
                stop_crawling_flag.set()
                break

            logger.info(f"{current_thread} Crawling: {page_url} (Visited {current_pages_crawled}/{MAX_PAGES_TO_CRAWL})")


        html_content, links = fetch_and_parse(page_url)

        if html_content:
            with crawled_html_content_lock:
                crawled_html_content[page_url] = html_content

        for link in links:
            with visited_urls_lock:
                if not stop_crawling_flag.is_set() and link not in visited_urls:
                    url_queue.append(link)

        time.sleep(CRAWL_DELAY)

    logger.info(f"{current_thread} exiting.")

#endregion

if __name__ == "__main__":
    main()