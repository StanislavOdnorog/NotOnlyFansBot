import asyncio

import grequests
from alive_progress import alive_bar
from bs4 import BeautifulSoup

from core.config import config
from core.logger import logger
from db.database import Database
from db.queries import Queries


class ModelsManager:
    def __init__(self):
        self.initialize_database()
        self.get_pages_number()

    def get_pages_number(self):
        response = grequests.map([grequests.get(config.MAIN_URL)])[0]
        soup = BeautifulSoup(response.text, "html.parser")
        self.pages = int(soup.find_all("a", class_="page-link")[2].text)

    def initialize_database(self):
        Database.initialize(
            database=config.DATABASE,
            host=config.DB_HOST,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
        )

    async def update_models(self):
        urls = [config.PAGE_URL + str(page) for page in range(1, self.pages + 1)]
        rs = [grequests.get(url) for url in urls]

        with alive_bar(len(rs), force_tty=True, title="Updating Models:") as bar:
            for r in grequests.map(rs):
                page_models = await self.get_models(r)
                await Queries.save_models(page_models)
                bar()

    async def update_materials(self):
        urls = Queries.view_models()[:500]
        with alive_bar(len(urls), force_tty=True, title="Updating Materials:") as bar:
            rs = (grequests.get(config.MODELS_URL + str(*url)) for url in urls)
            for r in grequests.map(rs):
                materials = await self.get_model_materials(r)
                await Queries.save_model_materials(materials)
                bar()

    async def get_models(self, response: grequests.AsyncRequest):
        soup = BeautifulSoup(response.text, "html.parser")

        page_models = set()
        page_models.update(
            el.text.lstrip("@") for el in soup.find_all("span", class_="date")
        )
        return page_models

    async def get_model_materials(self, response: grequests.AsyncRequest):
        soup = BeautifulSoup(response.text, "html.parser")

        materials = {}
        materials["model"] = await self.get_model_username(soup)
        materials["photos"] = await self.get_materials_num(soup, id="photos-tab")
        materials["videos"] = await self.get_materials_num(soup, id="videos-tab")
        materials["bio"] = await self.get_bio(soup)
        materials["img_ref"] = await self.get_img_reg(soup)

        return materials

    async def get_model_username(self, soup):
        material = soup.find("div", class_="actor-movie").text.strip("@")

        return material

    async def get_materials_num(self, soup, id=None):
        material = soup.find("a", {"id": id}).text.split("(")[1].split(f")")[0]
        try:
            return str(round(eval(material.replace("K", " * 1000"))))
        except TypeError as Err:
            logger.error(Err)
            return "ERROR"

    async def get_bio(self, soup):
        material = soup.find("div", class_="actor-description descriptions").text

        return material.strip().split("-------")[0].rstrip().replace("'", "''")

    async def get_img_reg(self, soup):
        material = soup.find("img", class_="model-thumbnail")["src"]

        return material


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(ModelsManager().update_materials()) for _ in range(10)]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
    # m.update_models()
    # m.update_materials()
    # m.format_all_bio()
