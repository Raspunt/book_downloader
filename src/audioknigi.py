import re
import os
import base64
import urllib.parse
import json
import uuid

from bs4 import BeautifulSoup
import requests



class AudioKnigi():
    
    def __init__(self):
        self.save_folder = "books"
        self.main_url = "https://audioknigi.pro/audioknigi/37558-igraty_-chtoby-vyghity-4-inferno.html"

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


    
    
    def download_playlist(self, playlist, title):
        os.makedirs(self.save_folder, exist_ok=True)

        book_folder = os.path.join(self.save_folder, title)
        os.makedirs(book_folder, exist_ok=True)

        for mp3Book in playlist:
            url = mp3Book["file"]
            part_title = mp3Book["title"].replace(" ", "_")
            filename = f"{part_title}.mp3"
            path = os.path.join(book_folder, filename)

            print(f"Скачиваю: {url} -> {path}")
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)




ak = AudioKnigi()

for i in range(1,1000):
    books = ak.get_books_by_page(i)

    for book in books:
        playlist = ak.get_playlist(book['url'])
        ak.download_playlist(playlist,book['name'])

        