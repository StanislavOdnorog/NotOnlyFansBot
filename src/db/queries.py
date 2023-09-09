import os
from time import time

from db.cursor import Cursor


class Queries:
    @staticmethod
    async def save_models(models):
        with Cursor() as c:
            c.execute(
                f"""INSERT INTO public.notonlyfans_db (model) VALUES {"('" + f"'), ('".join(models) + "')"} ON CONFLICT DO NOTHING"""
            )

    @staticmethod
    async def save_model_materials(materials):
        with Cursor() as c:
            c.execute(
                f"""UPDATE public.notonlyfans_db SET photos = '{materials["photos"]}', videos = '{materials["videos"]}', bio = '{materials["bio"]}', img_ref = '{materials["img_ref"]}' WHERE model = '{materials["model"]}'"""
            )

    @staticmethod
    def view_models():
        with Cursor() as c:
            c.execute("SELECT Model FROM public.notonlyfans_db")
            record_table = c.fetchall()
        return record_table
