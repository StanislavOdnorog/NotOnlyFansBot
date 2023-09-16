import grequests

from core.config import config
from core.logger import logger


class MaterialsManager:
    def __init__(self):
        pass

    async def get_material_url(
        self, model, materials_num, material_type, current_number
    ):
        """
        Function return url of materials for given model according to materials number and size

        Args:
            model (string): Takes model username
            materials_num (string | int): Takes number of material
            materials_type (string): Takes "photos" or "videos" parameter

        Returns:
            string: returns url
        """
        materials_num = int(materials_num)
        if materials_num == 0:
            if material_type == "videos":
                return config.NO_MATERIAL_URL, None
            elif material_type == "photos":
                return config.NO_MATERIAL_URL
        else:
            url = config.MODELS_URL + f"{model}"

            href = await self.get_response(
                url, materials_num, material_type, current_number
            )

            href = href.json()[
                await self.get_material_number(materials_num, current_number)
            ]["thumbnail"]

            if href == None:
                return config.NO_MATERIAL_URL

            if material_type == "videos":
                video_url = (
                    config.PLAYER_REF
                    + url
                    + "/video/"
                    + href.split("/")[-2]
                    + config.PLAYER_PARAMS
                )
                response = href, video_url
                grequests.map([grequests.get(video_url)])
            elif material_type == "photos":
                try:
                    response = href[:-8] + ".jpg"
                except TypeError as Err:
                    logger.error(Err)
                    response = href

            return response

    async def get_response(self, url, materials_num, material_type, current_number):
        page = await self.get_page_number(materials_num, current_number)
        attributes = await self.get_req_params(page, material_type)
        response = grequests.map(
            [grequests.get(url, params=attributes[0], headers=attributes[1])]
        )[0]
        try:
            if response.status_code != 200:
                return None
        except AttributeError as Err:
            logger.error(Err)
            return None
        return response

    async def get_page_number(self, materials_num, current_number):
        current_number %= materials_num
        current_number //= 49
        return current_number + 1

    async def get_material_number(self, materials_num, current_number):
        current_number %= materials_num
        return current_number % 48

    async def get_req_params(self, page, material_type):
        query_params = {
            "page": str(page),
            "type": material_type,
            "order": "0",
        }
        headers = {
            "User-Agent": config.USER_AGENT_HEADER,
            "X-Requested-With": "XMLHttpRequest",
        }
        return query_params, headers
