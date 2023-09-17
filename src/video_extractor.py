import urllib.request
import os
import shutil
import requests
from bs4 import BeautifulSoup
from requests_html import AsyncHTMLSession
import asyncio

async def main():
    url = "https://9xbuddy.in/process?url=https://leakedzone.com/lanarhoadesx3/video/1880191"

    asession = AsyncHTMLSession()
    respond = await asession.get(url)
    await respond.html.arender()
    print(respond.text.split("max-w-sm")[0])

loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()
#
# my_lessons = [
# "https://cdn12-leak.camhdxx.com/GTVhpexB_zEvTbxYDmFIEw==,1694912647/14806/4899312/video"
# ]
#
# lesson_dir = "my_vids"
# try:
#     shutil.rmtree(lesson_dir)
# except:
#     print("ok")
#
# os.makedirs(lesson_dir)
# os.chdir(lesson_dir)
#
# for lesson, dwn_link in enumerate(my_lessons):
#     print ("downloading lesson  %d.. " % (lesson), dwn_link)
#     file_name = '%04d.ts' % lesson
#     f = open(file_name, 'ab')
#     for x in range(0, 1200):
#         try:
#             rsp = urllib.request.urlopen(dwn_link + f"{x}.ts")
#         except:
#             break
#         file_name = '%d.ts' % lesson
#         print("downloading  %d.ts" % (x))
#         f.write(rsp.read())
#     f.close()

