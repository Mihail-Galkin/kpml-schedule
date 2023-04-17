import os
from datetime import datetime
from json import load, dump

import requests
import schedule as schedule
import vk_api
from bs4 import BeautifulSoup
from pdf2image import convert_from_bytes
from vk_api import VkUpload

vk_session = vk_api.VkApi(token=os.getenv("TOKEN"))

upload = VkUpload(vk_session)

base_url = "https://kpml.ru/"
url = "https://kpml.ru/pages/raspisanie/izmeneniya-v-raspisanii"


def check_updates():
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    pdfs = [base_url + i["href"] for i in soup.find_all("a") if i["href"].endswith(".pdf")]
    with open("old.json", "r") as f:
        old = load(f)

    to_send = list(set(pdfs) - set(old))
    if to_send:
        photos = []
        print(f"[{datetime.now()}] Loading changes: {len(to_send)}")
        for link in to_send:
            page = convert_from_bytes(requests.get(link).content, 500)[0]
            path = f"temp/{link.rsplit('/', maxsplit=1)[-1].rsplit('.', maxsplit=1)[0]}.png"
            page.save(path, "PNG")
            photos.append(path)
        photo_list = upload.photo_wall(photos)
        attachment = ','.join('photo{owner_id}_{id}'.format(**item) for item in photo_list)

        vk_session.method("wall.post", {
            'owner_id': os.getenv("GROUP_ID"),
            'attachments': attachment,
            'signed': 0,
            'from_group': 1,
        })

        for file in photos:
            os.remove(file)

        with open("old.json", "w") as f:
            dump(pdfs, f)

        print("Images sent")


schedule.every(10).minutes.do(check_updates)

while True:
    schedule.run_pending()
