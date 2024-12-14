import requests
from bs4 import BeautifulSoup

def download_books(homepage):
    """Downloads books from the specified homepage."""

    with requests.Session() as session:
        home_page = session.get(homepage)
        soup = BeautifulSoup(home_page.content, 'html.parser')

        book_urls = []
        for book_container in soup.find_all('div', {'class': 'bookContainer grow'}):
            for link in book_container.find_all('a'):
                book_url = f"{homepage}{link['href']}"
                book_urls.append(book_url)

        for book_front in book_urls:
            book_page = session.get(book_front)
            book_soup = BeautifulSoup(book_page.content, 'html.parser')

            for link in book_soup.find('div', {'id': 'frontpage'}).find_all('a'):
                download_payload = f"{book_front}/{link['href']}"
                if '.pdf' in download_payload:
                    download_link = download_payload
                    print(f"Downloading {link['href']}...")

                    response = session.get(download_link)
                    with open(link['href'], 'wb') as f:
                        f.write(response.content)

if __name__ == "__main__":
    homepage = 'http://books.goalkicker.com/'
    download_books(homepage) 

