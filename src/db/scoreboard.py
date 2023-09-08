from lib.cursor import Cursor
from lib.logger import Logger


class Scoreboard:

    @staticmethod
    @Logger.log
    def save_record(name, score):
        with Cursor() as c:
            c.execute(
                f"INSERT INTO public.snake (username, score) VALUES ('{name}', {score})")

    @staticmethod
    @Logger.log
    def view_record():
        with Cursor() as c:
            c.execute(
                "SELECT username, score FROM public.snake ORDER BY score DESC LIMIT 5")
            record_table = c.fetchall()
        return record_table
