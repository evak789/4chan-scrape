import os
import requests
import shutil
from bs4 import BeautifulSoup
import progressbar

URL = "https://boards.4chan.org/pol"
IMAGE_PREFIX = "//i.4cdn.org/pol/"

class Scraper:
    def __init__(self):
        # initialize members
        self._thread_ids = [] # list of all thread ID's
        self._image_map = {} # map of image URL -> image filename

        # make the "data/images" directory, if necessary
        os.makedirs("images", mode=0o777, exist_ok=True)

    def read_pages(self):
        # there are always 10 pages
        suffixes = ["", "/2", "/3", "/4", "/5", "/6", "/7", "/8", "/9", "/10"]
        widgets = [
            progressbar.FormatLabel("Page {value}/{max_value}", new_style=True),
            progressbar.GranularBar(),
            progressbar.ETA()]
        with progressbar.ProgressBar(max_value=len(suffixes), widgets=widgets) as bar:
            for i, suffix in enumerate(suffixes):
                bar.update(i)
                page_url = URL + suffix
                self._download_page(page_url)

    def _download_page(self, page_url):
        # get the page
        page = requests.get(page_url) 
        soup = BeautifulSoup(page.text, "html.parser")

        # record all the thread ID's
        threads = list(soup.find_all("div",attrs={"class":"thread"}))
        for thread in threads:
            thread_id = thread.attrs["id"][1:]
            self._thread_ids.append(thread_id)

    def read_threads(self):
        widgets = [
            progressbar.FormatLabel("Thread {value}/{max_value}", new_style=True),
            progressbar.GranularBar(),
            progressbar.ETA()]
        with progressbar.ProgressBar(max_value=len(self._thread_ids), widgets=widgets) as bar:
            for i, thread_id in enumerate(self._thread_ids):
                bar.update(i)
                self._download_thread(thread_id)

    def _download_thread(self, thread_id):
        # download the page of the thread
        thread_url = URL + "/thread/" + thread_id
        page = requests.get(thread_url)    

        # look for images
        page_source = page.text
        soup = BeautifulSoup(page_source, "html.parser")
        image_list = []
        for img in soup.find_all("img"):
            img_src = img.attrs["src"]
            if img_src.startswith(IMAGE_PREFIX):
                img_filename = img_src[len(IMAGE_PREFIX):]
                image_list.append(img_filename)

                # also get the full-size image
                if img_filename.endswith("s.jpg"):
                    img_full_name = img_filename.replace("s.jpg", ".jpg")
                    image_list.append(img_full_name)

        # make a map of image URL -> image filename
        image_map = {}
        for img in image_list:
            img_url = IMAGE_PREFIX + img
            img_filename = "images/" + img
            image_map[img_url] = img_filename

        # replace the image links in the source
        for img_url, img_filename in image_map.items():
            page_source = page_source.replace(img_url, img_filename)

        # write the page to a file
        thread_filename = self._thread_path(thread_id)
        with open(thread_filename, "w") as fp:
            fp.write(page_source)

        # check which images need to be downloaded
        for img_url, img_filename in image_map.items():
            img_path = self._image_path(img_filename)
            if not os.path.exists(img_path):
                self._image_map[img_url] = img_filename

    def download_images(self):
        widgets = [
            progressbar.FormatLabel("Image {value}/{max_value}", new_style=True),
            progressbar.GranularBar(),
            progressbar.ETA()]
        with progressbar.ProgressBar(max_value=len(self._image_map), widgets=widgets) as bar:
            for i, img_url in enumerate(self._image_map.keys()):
                bar.update(i)
                img_filename = self._image_map[img_url]
                self._download_image(img_url, img_filename)

    def _download_image(self, img_url, img_filename):
        img = requests.get("https:" + img_url, stream=True)
        img_path = self._image_path(img_filename)
        with open(img_path, "wb") as fp:
            shutil.copyfileobj(img.raw, fp)

    def _thread_path(self, thread_id):
        return "data/" + thread_id + ".html"
    
    def _image_path(self, img_filename):
        return "data/" + img_filename # already has "images/" in it

def main():
    scraper = Scraper()
    scraper.read_pages()
    scraper.read_threads()
    scraper.download_images()

main()
