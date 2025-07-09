# webcrawler
Web crawler project

## requirements

- Python 3.13.5

Instead of installing dependencies manually, you can use the provided `install_deps.py` script to install all required packages. Simply run:

    python install_deps.py

This script will handle installing all necessary dependencies for the project.

# application overview

This application will crawl urls starting with the provided URL.

Revisited URLs is not allowed and you will be alerted as such. Providing a new (unvisited) URL will allow the crawler to
continue its work.

Once the crawling has completed, you can begin indexing to rank these URLs to help the query engine properly rank them.

## how to run the crawler and indexer

To run these seperate services, you can use the provided `.bat` files:

    - .\crawl & .\index (using Powershell)
    - crawl & index (using Command Prompt)
