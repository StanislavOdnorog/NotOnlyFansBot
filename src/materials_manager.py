import random

import grequests
from core.config import config


class MaterialsManager:
    def __init__(self):
        pass

    async def get_material_url(self, model, materials_num, material_type):
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
            else:
                return config.NO_MATERIAL_URL

        else:
            url = config.MODELS_URL + f"{model}"
            href = await self.get_response(url, materials_num, material_type)
            href = href[0].json()[await self.get_random_material(materials_num)][
                "thumbnail"
            ]

        if material_type == "videos":
            video_url = config.PLAYER_REF + url + "/video/" + href.split("/")[-2]
            video_url = await self.get_short_link(video_url)
            response = href, video_url
        elif material_type == "photos":
            response = href[:-8] + ".jpg"

        return response

    async def get_response(self, url, materials_num, material_type):
        random_page = await self.get_random_page(materials_num)
        attributes = await self.get_req_params(random_page, material_type)
        response = grequests.map(
            [
                grequests.get(
                    url,
                    params=attributes[0],
                    headers=attributes[1],
                )
            ]
        )
        return response

    async def get_random_page(self, materials_num):
        if materials_num % 48 == 0 or materials_num // 48 == 0:
            random_page = random.randint(1, materials_num // 48 + 1)
        else:
            random_page = materials_num // 48

        return random_page

    async def get_random_material(self, materials_num):
        random_photo = random.randint(0, 48)
        if materials_num % 48 == 0 or materials_num // 48 == 0:
            random_photo = random_photo % materials_num
        return random_photo

    async def get_req_params(self, random_page, material_type):
        query_params = {
            "page": str(random_page),
            "type": material_type,
            "order": "0",
        }
        headers = {
            "User-Agent": config.USER_AGENT_HEADER,
            "X-Requested-With": "XMLHttpRequest",
        }
        return query_params, headers

    async def get_short_link(self, url):
        query_data = {"url": url}
        query_headers = {config.SHORT_LINK_API_DATA: config.SHORT_LINK_API_TOKEN}
        response = grequests.map(
            [
                grequests.post(
                    config.SHORT_LINK_API_SITE, data=query_data, headers=query_headers
                )
            ]
        )[0]

        return response.json()["short_url"]


# if __name__ == "__main__":
#     print(MaterialsManager().get_material_url("amouranth", "452", "videos"))
