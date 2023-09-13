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
            c.execute("SELECT model FROM public.notonlyfans_db ORDER BY photos DESC")
            record_table = c.fetchall()
        return record_table

    @staticmethod
    def get_random_model():
        with Cursor() as c:
            c.execute("SELECT * FROM public.notonlyfans_db ORDER BY RANDOM()")
            record = c.fetchone()
        return record

    @staticmethod
    def get_model(model):
        if model:
            with Cursor() as c:
                c.execute(
                    f"SELECT * FROM public.notonlyfans_db WHERE model = '{model}'"
                )
                record = c.fetchone()
            return record

    @staticmethod
    def get_alike_models(model):
        if model:
            with Cursor() as c:
                c.execute(
                    f"SELECT * from notonlyfans_db where levenshtein(model, '{model}') between 1 and 3 order by levenshtein(model, '{model}') asc limit 5"
                )
                record = c.fetchall()
            return record

    @staticmethod
    def add_user(user_id):
        if user_id:
            with Cursor() as c:
                c.execute(
                    f"INSERT INTO users_db(user_id, user_endsub) VALUES ('{user_id}', CURRENT_DATE + interval '5 day') ON CONFLICT DO NOTHING"
                )

    @staticmethod
    def prolong_subsription(user_id):
        if user_id:
            with Cursor() as c:
                c.execute(
                    f"UPDATE users_db SET user_endsub = CURRENT_DATE WHERE user_id = '{user_id}' AND user_endsub < CURRENT_DATE"
                )
                c.execute(
                    f"UPDATE users_db SET user_endsub = user_endsub + interval '1 month' WHERE user_id = '{user_id}'"
                )

    @staticmethod
    def is_subsribed(user_id):
        if user_id:
            with Cursor() as c:
                c.execute(
                    f"SELECT EXISTS(SELECT * FROM users_db where user_id='{user_id}' and user_endsub >= CURRENT_DATE)"
                )
                record = c.fetchone()
            return record[0]

    @staticmethod
    def get_endsub_date(user_id):
        if user_id:
            with Cursor() as c:
                c.execute(
                    f"UPDATE users_db SET user_endsub = CURRENT_DATE  - interval '1 day' WHERE user_id = '{user_id}' AND user_endsub < CURRENT_DATE"
                )
                c.execute(f"SELECT user_endsub FROM users_db where user_id='{user_id}'")
                record = c.fetchone()
            return record[0].strftime("%d.%m.%y")
