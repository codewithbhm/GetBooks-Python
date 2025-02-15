import os
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor
import logging
import time

class GoalKickerParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.book_links = []
        self.pdf_links = []
        self.in_div = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'div' and 'class' in attrs and 'bookContainer' in attrs['class']:
            self.in_div = True
        elif self.in_div and tag == 'a' and 'href' in attrs:
            self.book_links.append(attrs['href'])
        elif tag == 'a' and 'href' in attrs and attrs['href'].endswith('.pdf'):
            self.pdf_links.append(attrs['href'])

    def handle_endtag(self, tag):
        if tag == 'div' and self.in_div:
            self.in_div = False

def fetch(url, retries=3):
    attempt = 0
    while attempt < retries:
        try:
            with urllib.request.urlopen(url) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            logging.error(f"Error fetching {url}: {e}")
            attempt += 1
            time.sleep(2)
    return ''

def sanitize_filename(url):
    # Extract the filename from the URL
    filename = os.path.basename(urlparse(url).path)
    # Remove any directory traversal characters
    return os.path.basename(filename)

def download_pdf(pdf_url):
    filename = sanitize_filename(pdf_url)
    try:
        with urllib.request.urlopen(pdf_url) as response:
            with open(filename, 'wb') as f:
                f.write(response.read())
        logging.info(f"Downloaded: {filename}")
    except Exception as e:
        logging.error(f"Error downloading {pdf_url}: {e}")

def main():
    logging.basicConfig(level=logging.INFO)
    base_url = 'http://books.goalkicker.com/'
    homepage_html = fetch(base_url)
    if not homepage_html:
        return

    parser = GoalKickerParser()
    parser.feed(homepage_html)

    book_urls = [urljoin(base_url, link) for link in parser.book_links]

    for book_url in book_urls:
        book_html = fetch(book_url)
        if not book_html:
            continue
        parser.feed(book_html)

    pdf_urls = [urljoin(base_url, link) for link in parser.pdf_links]

    with ThreadPoolExecutor() as executor:
        executor.map(download_pdf, pdf_urls)

if __name__ == '__main__':
    main()
