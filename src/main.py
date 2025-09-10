import os
import re
import sys
import json
import requests
from typing import List, Tuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from checkpoint import Checkpoint

# start_url = "https://audiokniga-online.ru/popadancy/752-igrat-chtoby-zhit-sryv.html"
main_site = "https://audiokniga-online.ru/"
save_folder = "D:/всякое/books"



def get_book(playlist_url: str) -> List[Tuple[str, str]]:
    try:
        res = requests.get(playlist_url, timeout=5)
        res.raise_for_status()

        book_chapters = []
        for ch in res.json():
            title = ch.get("title") or "chapter"
            file_url = ch.get("file")
            if file_url:
                book_chapters.append((title, file_url))

        return book_chapters

    except Exception as e:
        print(f"Ошибка при загрузке книги: {e}")
        return []

def safe_filename(s: str) -> str:
    return "".join(c for c in s if c.isalnum() or c in " _-").strip()


def download_book(book: List[Tuple[str, str]], url: str):
    if not book:
        print("Книга пустая, нечего скачивать")
        return

    raw_name = book[0][0]
    safe_name = safe_filename(raw_name)

    slug = os.path.splitext(os.path.basename(urlparse(url).path))[0]

    save_dir = os.path.join(save_folder, f"{safe_name}_{slug}")
    os.makedirs(save_dir, exist_ok=True)


    for idx, (title, file_url) in enumerate(book, start=1):
        try:
            safe_title = safe_filename(title)
            filename = f"{idx:03d}_{safe_title}.mp3"
            filepath = os.path.join(save_dir, filename)

            if os.path.exists(filepath):
                print(f"[SKIP] {filename} уже существует")
                continue

            res = requests.get(file_url, timeout=10, stream=True)
            res.raise_for_status()

            with open(filepath, "wb") as f:
                for chunk in res.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            print(f"[OK] {filename}")
        except Exception as e:
            print(f"[ERR] {file_url}: {e}")

def find_playlist(book_url) -> str | None:
    try:
        response = requests.get(book_url, timeout=5)
        response.raise_for_status()

        html = response.text
        urls = re.findall(r'https?://[^\s"\']+?\.php[^\s"\']*', html)
        rel_urls = re.findall(r'["\']([^"\']+?\.php[^\s"\']*)["\']', html)
        rel_urls = [urljoin(book_url, u) for u in rel_urls]

        for u in set(urls + rel_urls):
            if "playlist" in u:
                return u

        return None

    except Exception as e:
        return None


def get_list_books(page_url: str) -> list[str]:
    try:
        res = requests.get(page_url, timeout=5)
        res.raise_for_status()
    except Exception as e:
        print(f"[ERR] Не удалось загрузить {page_url}: {e}")
        return []

    soup = BeautifulSoup(res.text, "lxml")
    hrefs = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "popadancy" in href and href.endswith(".html"):
            hrefs.append(urljoin(page_url, href))
    return list(set(hrefs))


def run(max_pages: int = 5):
    checkpoint = Checkpoint(save_folder)
    checkpoint_list = checkpoint.load_checkpoint()

    for page in range(1, max_pages + 1):
        page_url = f"https://audiokniga-online.ru/page/{page}"
        print(f"\n=== Страница {page_url} ===")

        books = get_list_books(page_url)
        if not books:
            print("Книг не найдено, возможно страница пустая")
            continue

        for book_url in books:
            print(book_url)

            if book_url in checkpoint_list:
                print(f"[SKIP] {book_url} уже в чекпоинте")
                continue

            playlist_url = find_playlist(book_url)
            if not playlist_url:
                print("playlist не найден")
                continue

            book = get_book(playlist_url)
            download_book(book, book_url)

            checkpoint_list.add(book_url)
            checkpoint.save_checkpoint(checkpoint_list)


if __name__ == "__main__":
    run(100)