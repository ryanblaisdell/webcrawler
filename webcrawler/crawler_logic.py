import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from bs4.element import Tag
from database.db import save_page, is_url_visited, mark_url_visited
import logging
import threading
import time

# TODO: 
# - clean up the worker function to make it more readable; move logic into seperate functions

logger = logging.getLogger(__name__)

USER_AGENT = "example.com"

def fetch_and_parse(page_url: str) -> tuple[str, list]:
    """
    Fetches the HTML content of a URL and extracts all internal Wikipedia links.
    """
    import requests
    headers = {"User-Agent": USER_AGENT}
    html_content = ""
    links = []

    try:
        response = requests.get(page_url, headers=headers, timeout=10)
        response.raise_for_status()
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
    Only returns English Wikipedia article links, skipping citation/reference links.
    """
    found_links = []
    soup = BeautifulSoup(html_content, 'html.parser')
    for link_tag in soup.find_all('a', href=True):
        if not isinstance(link_tag, Tag):
            continue
        
        raw_link = link_tag.get('href')
        
        if not isinstance(raw_link, str):
            continue

        if raw_link.startswith("#cite_note"):
            continue
        
        resolved_url = urljoin(base_url, raw_link)
        parsed_resolved_url = urlparse(resolved_url)

        if (
            parsed_resolved_url.hostname == "en.wikipedia.org"
            and parsed_resolved_url.path.startswith("/wiki/")
            and ":" not in parsed_resolved_url.path
            and "#" not in parsed_resolved_url.fragment
        ):
            found_links.append(resolved_url)
            
    return found_links

def extract_page_content(html_content: str) -> str:
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator=" ")
    words = re.findall(r'\w+', text)
    page_text = ",".join(words)
    return page_text

def worker(url_queue, visited_urls, visited_urls_lock, stop_crawling_flag, MAX_PAGES_TO_CRAWL, CRAWL_DELAY):
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
            if page_url in visited_urls or is_url_visited(page_url):
                continue
            visited_urls.add(page_url)
            mark_url_visited(page_url)
            current_pages_crawled = len(visited_urls)
            if current_pages_crawled >= MAX_PAGES_TO_CRAWL:
                logger.info(f"{current_thread}: Max pages ({MAX_PAGES_TO_CRAWL}) reached. Signalling stop.")
                stop_crawling_flag.set()
                break
            logger.info(f"{current_thread} Crawling: {page_url} (Visited {current_pages_crawled}/{MAX_PAGES_TO_CRAWL})")

        html_content, links = fetch_and_parse(page_url)

        if html_content:
            save_page(page_url, html_content)

        for link in links:
            with visited_urls_lock:
                if not stop_crawling_flag.is_set() and link not in visited_urls:
                    url_queue.append(link)

        time.sleep(CRAWL_DELAY)
    logger.info(f"{current_thread} exiting.")
