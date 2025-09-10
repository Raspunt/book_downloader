import os
import multiprocessing as mp

from audiokniga import AudioKniga
from audioknigi import AudioKnigi

save_folder = "D:/всякое/books"

def run_audiokniga(save_folder, max_pages):
    ak = AudioKniga(save_folder)
    ak.run(max_pages)

def run_audioknigi(save_folder, max_pages):
    agi = AudioKnigi(save_folder)
    agi.run(max_pages)

if __name__ == "__main__":
    os.makedirs(save_folder, exist_ok=True)

    max_pages = 1000

    p = mp.Process(target=run_audiokniga, args=(save_folder, max_pages))
    p.start()

    # run_audiokniga(save_folder,max_pages)
    run_audioknigi(save_folder, max_pages)

    p.join()  
