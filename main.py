import asyncio
import aiohttp
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

async def fetch(session: ClientSession, url: str) -> str:
    """Fetch the content of a URL asynchronously."""
    try:
        async with session.get(url, timeout=10) as response:
            response.raise_for_status()
            return await response.text()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

async def get_book_urls(session: ClientSession, homepage: str) -> list:
    """Extract book page URLs from the homepage."""
    content = await fetch(session, homepage)
    if not content:
        return []
    
    soup = BeautifulSoup(content, 'html.parser')
    book_urls = []
    for container in soup.find_all('div', class_='bookContainer grow'):
        for a in container.find_all('a', href=True):
            book_url = urljoin(homepage, a['href'])
            book_urls.append(book_url)
    return book_urls

async def get_pdf_links(session: ClientSession, book_url: str) -> list:
    """Extract PDF download links from a book page."""
    content = await fetch(session, book_url)
    if not content:
        return []
    
    soup = BeautifulSoup(content, 'html.parser')
    frontpage = soup.find('div', id='frontpage')
    if not frontpage:
        print(f"Frontpage not found for {book_url}")
        return []
    
    pdf_links = []
    for a in frontpage.find_all('a', href=True):
        pdf_url = urljoin(book_url, a['href'])
        if '.pdf' in pdf_url.lower():
            pdf_links.append(pdf_url)
    return pdf_links

async def download_pdf(session: ClientSession, pdf_url: str) -> None:
    """Download a single PDF file."""
    filename = os.path.basename(pdf_url)
    if not filename:
        print(f"Cannot determine filename for {pdf_url}")
        return
    try:
        async with session.get(pdf_url, timeout=10) as response:
            response.raise_for_status()
            content = await response.read()
        with open(filename, 'wb') as f:
            f.write(content)
        print(f"Downloaded {filename}")
    except Exception as e:
        print(f"Error downloading {pdf_url}: {e}")

async def main(homepage: str):
    """Main routine to gather and download all PDFs concurrently."""
    async with aiohttp.ClientSession() as session:
        book_urls = await get_book_urls(session, homepage)
        if not book_urls:
            print("No book URLs found.")
            return

        # Gather PDF links from all book pages concurrently.
        pdf_links_nested = await asyncio.gather(
            *[get_pdf_links(session, book_url) for book_url in book_urls]
        )
        # Flatten the list of lists.
        pdf_links = [pdf for sublist in pdf_links_nested for pdf in sublist]
        if not pdf_links:
            print("No PDF links found.")
            return

        print(f"Found {len(pdf_links)} PDFs. Starting downloads...")

        # Download all PDFs concurrently.
        await asyncio.gather(
            *[download_pdf(session, pdf_url) for pdf_url in pdf_links]
        )

if __name__ == "__main__":
    homepage = 'http://books.goalkicker.com/'
    asyncio.run(main(homepage))
