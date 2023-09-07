import requests
import json
import pandas as pd
import time
import os
import re
import math


class ModelsManager():
    def __init__(self):
        self.pages = requests.get("https://leakedzone.com/creators").text.\
                                split("class=\"page-item hidden-xs\"")[1].\
                                                        split("</a>")[0].\
                                                            split("\">")[1]
        self.models_list = []
        self.photos_list = []
        self.videos_list = []
        self.img_ref_list = []
        self.bio_list = []
        self.est_time = 0
        self.all_models_db = pd.DataFrame()


    def update_models(self):    
        for curr_page in range(1, int(self.pages)+1):
            self.get_models(index=curr_page, max=int(self.pages))
        self.save_database()


    def update_materials(self):
        print("...")
        self.videos = pd.read_csv("models.csv")['Videos'].to_list() 
        self.photos = pd.read_csv("models.csv")['Photos'].to_list() 
        self.models_list = pd.read_csv("models.csv")['Model'].to_list()
        self.bios = pd.read_csv("models.csv")['Bio'].to_list()
        self.img_refs = pd.read_csv("models.csv")['Img_ref'].to_list()

        for index, model in enumerate(self.models_list):
            if str(self.photos[index]) == "nan" and str(self.videos[index]) == "nan":
                self.get_model_materials(index=index, model=model, max=len(self.models_list))
            else:
                self.photos_list.append(self.photos[index])
                self.videos_list.append(self.videos[index])
                self.img_ref_list.append(self.img_refs[index])
                self.bio_list.append(self.bios[index])
                os.system("clear")
                print(f"Collecting materials : [{index}/{len(self.models_list)}] : Already up to date")

            self.save_database()

        self.format_all_bio()
        self.save_database()


    def save_database(self): 
        df = pd.DataFrame({'Model': self.models_list})
        df = pd.concat([df, pd.DataFrame(self.photos_list, columns=['Photos'])], axis=1)
        df = pd.concat([df, pd.DataFrame(self.videos_list, columns=['Videos'])], axis=1)
        df = pd.concat([df, pd.DataFrame(self.img_ref_list, columns=['Img_ref'])], axis=1)
        df = pd.concat([df, pd.DataFrame(self.bio_list, columns=['Bio'])], axis=1)
        df.to_csv("models.csv")


    def time_bar_decorator(text):
        def inner(func):
            def wrapper(*args, **kwargs):
                cl = args[0]
                index = kwargs["index"]
                max = kwargs["max"]

                start_time = time.time()
                dots = ""
                for _ in range(index % 5):
                    dots += '.'

                os.system("clear")
                print(f"{text} : [{index}/{max}] : " + str(cl.est_time) + f" seconds left{dots}")

                func(*args, **kwargs)
                end_time = time.time() - start_time
                
                cl.est_time = round((cl.est_time + end_time * (max - index)) / 2.0)

            return wrapper
        return inner
    

    @time_bar_decorator("Updating models")
    def get_models(self, index=None, max=None):
        req = requests.get(f"https://leakedzone.com/creators?page={index}")

        for text in req.text.split("<span class=\"date\">@")[1:]:
            self.models_list.append(text.split("</span>")[0])


    @time_bar_decorator("Collecting materials")
    def get_model_materials(self, index=None, model=None, max=None):
        req = requests.get(f"https://leakedzone.com/{model}")
        self.photos_list.append(req.text.split("Photos (")[1].split(")</a>")[0])
        self.videos_list.append(req.text.split(">Videos (")[1].split(")</a>")[0])
        self.img_ref_list.append(req.text.split("<img class=\"model-thumbnail\" src=\"")[1].split("\" alt")[0])

        self.bio_list.append(re.sub("<br />", "\n", req.text.\
                        split("div class=\"actor-description")[1].\
                        split("<p>")[1].\
                        split("-----------")[0]))
        

    def format_all_bio(self):
        for index, temp_bio in enumerate(self.models_list):
            temp_bio = re.sub("<br>", "\n", temp_bio)

            copyright_list = ["copyright", "Copyright", "COPYRIGHT",\
                              "Do not leak", "Legal action", "By subscribing",\
                              "By purchasing", "copyrighted", "Copyrighted", "COPYRIGHTED", "DO NOT SCREENSHOT"]
            
            for element in copyright_list:
                if element in temp_bio:
                    temp_bio = temp_bio.split(element)[0]

            self.bio_list[index] = temp_bio
            

if __name__ == "__main__":
    m = ModelsManager()
    # m.update_models()
    m.update_materials()
    m.format_all_bio()
