import re
import os
import base64
import urllib.parse
import json
import uuid

from bs4 import BeautifulSoup
import requests

from checkpoint import Checkpoint



class AudioKnigi():
    
    def __init__(self,save_folder):
        self.save_folder = save_folder

    def get_books_by_page(self,page):
        res = requests.get(f"https://audioknigi.pro/audioknigi/page/{page}/")
        soup = BeautifulSoup(res.text, "lxml")

        print(f"Открываю страницу {page}")

        books = []
        for a in soup.find_all("a",class_="name-kniga"):
            books.append({
                "name":a.text.strip(),
                "url": a["href"]
            })
        print(f"Вижу {len(books)} книг!")

        return books



        

    def strDecode(self,data: str) -> str:
        chars = "PUhncLHApBrM7GvdqT4tNWRjemgak9oVzwZ8K1XDfY5bQOSlsF26yi0JCIuxE3+/="
        decoded_bytes = bytearray()
        i = 0

        data = "".join(c for c in data if c in chars)

        while i < len(data):
            enc1 = chars.index(data[i]); i += 1
            enc2 = chars.index(data[i]); i += 1
            enc3 = chars.index(data[i]); i += 1
            enc4 = chars.index(data[i]); i += 1

            chr1 = (enc1 << 2) | (enc2 >> 4)
            chr2 = ((enc2 & 15) << 4) | (enc3 >> 2)
            chr3 = ((enc3 & 3) << 6) | enc4

            decoded_bytes.append(chr1)
            if enc3 < 64:
                decoded_bytes.append(chr2)
            if enc4 < 64:
                decoded_bytes.append(chr3)

        return urllib.parse.unquote(decoded_bytes.decode("utf-8"))

    def get_playlist(self,url):
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "lxml")


        for sc in soup.find_all("script"):
            if sc.string and "playerjs1" in sc.string:
                match = re.search(r'strDecode\("([^"]+)"\)', sc.string)
                if match:
                    encoded = match.group(1)
                    json_data = json.loads(self.strDecode(encoded))
                    return json_data
        return []


    
    
    def safe_filename(self, name: str) -> str:
        return re.sub(r'[^a-zA-Zа-яА-Я0-9_\- ]', '_', name).strip()[:100]

    def download_playlist(self, playlist, title):
        if not playlist:
            print(f"[WARN] У книги '{title}' пустой плейлист, пропускаю")
            return False

        os.makedirs(self.save_folder, exist_ok=True)

        safe_title = self.safe_filename(title)
        book_folder = os.path.join(self.save_folder, safe_title)
        os.makedirs(book_folder, exist_ok=True)

        success = True
        for mp3Book in playlist:
            url = mp3Book.get("file")
            part_title = self.safe_filename(mp3Book.get("title", "part"))
            filename = f"{part_title}.mp3"
            path = os.path.join(book_folder, filename)

            if os.path.exists(path) and os.path.getsize(path) > 1024:
                print(f"[SKIP] {path} уже существует")
                continue

            try:
                print(f"[DL] {url} -> {path}")
                r = requests.get(url, stream=True, timeout=15)
                r.raise_for_status()

                with open(path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                print(f"[OK] {filename}")
            except Exception as e:
                print(f"[ERR] {url}: {e}")
                success = False

        return success


    def run(self, max_pages:int):
        checkpoint = Checkpoint(self.save_folder)
        checkpoint_list = checkpoint.load_checkpoint()

        for i in range(1,max_pages):
            books = self.get_books_by_page(i)

            for book in books:

                if book['url'] in checkpoint_list:
                    print(f"[SKIP] {book['url']} уже в чекпоинте")
                    continue

                playlist = self.get_playlist(book['url'])
                self.download_playlist(playlist,book['name'])

                checkpoint_list.add(book['url'])
                checkpoint.save_checkpoint(checkpoint_list)

                