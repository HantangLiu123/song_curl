import requests
from bs4 import BeautifulSoup
import re
import time
import json
import random

def get_all_artist_ids() -> list[int]:

    """get all artist ids from the saved hrefs list"""

    ARTIST_HREFS_PATH = "C:/Chris Liu/清华/25暑期/python-course/song_curl/saved_info/artist_hrefs.json"
    with open(ARTIST_HREFS_PATH, "r", encoding="utf-8") as f:
        hrefs_list = json.load(f)
    
    #extract the ids from the hrefs_list
    id_list = []
    for href in hrefs_list:
        _, id = re.split(r'id=', href, maxsplit=1)
        id = int(id)
        id_list.append(id)
    
    return id_list

def get_image(image_url: str, headers: dict[str, str], cookies: dict[str, str], name: str) -> None:

    """Getting the image using the url

    Getting the image from the url and storing in the local folder

    Params:
        image_url(str): the url used to make the request
        headers(dict[str, str]): the headers for the request
        cookies(dict[str, str]): the cookies for the request
        name(str): the artist's name

    Returns:
        None
    """

    response = requests.get(image_url, headers=headers, cookies=cookies)
    image = response.content
    INFO_OUT_DIR = 'C:/Chris Liu/清华/25暑期/python-course/song_curl/saved_info/artist_info/artist_images'
    OUT_PATH = f"{INFO_OUT_DIR}/{name}.jpg"
    with open(OUT_PATH, "wb") as f:
        f.write(image)

def analyze_response(response, headers: dict[str, str], cookies: dict[str, str]) -> None:

    """Analyze a response
    
    Analyze the response after getting the artist page, extract related info
    (e.g. name, alias, intro, etc.) and store them in a local json file

    Params:
        response: the response of the artist page request
        headers(dict[str, str]): headers using by the request
        cookies(dict[str, str]): cookies using by the request
    
    Returns:
        None
    """

    soup = BeautifulSoup(response.text, "lxml")

    #extracting info from artist
    artist = {}
    artist['name'] = soup.h2.text.strip()
    artist['alias'] = re.split(r';', soup.h3.text.strip())

    #further analyze the introduction block
    artist_intro_block = soup.find(class_="n-artdesc")
    artist_headers = artist_intro_block.find_all("h2")
    artist_paragraphs = artist_intro_block.find_all("p")
    artist_intro = {}
    for i in range(len(artist_headers)):
        header_name = artist_headers[i].text.strip()
        if re.search(r'简介$', header_name):
            artist_intro['intro'] = artist_paragraphs[i].text.strip()
        elif header_name == '演艺经历':
            artist_intro['history'] = artist_paragraphs[i].text.strip()
        elif header_name == '代表作品':
            artist_paragraph = artist_paragraphs[i].text.strip()
            master_work = re.split(r'●', artist_paragraph)
            if master_work[0] == "":
                master_work.remove("")
            artist_intro['master work'] = master_work
        elif header_name == '重要里程碑':
            artist_paragraph = artist_paragraphs[i].text.strip()
            milestones = re.split(r'●', artist_paragraph)
            if milestones[0] == "":
                milestones.remove("")
            artist_intro['milestones'] = milestones
    artist['intro'] = artist_intro

    #store info found
    INFO_OUT_DIR = 'C:/Chris Liu/清华/25暑期/python-course/song_curl/saved_info/artist_info/artist_intro'
    OUT_PATH = f"{INFO_OUT_DIR}/{artist['name']}.json"
    with open(OUT_PATH, "w", encoding='utf-8') as f:
        json.dump(artist, f, indent=4, sort_keys=False, ensure_ascii=False)

    #get the image after a small break
    time.sleep(random.random() + 1)
    image_url = soup.find_all("img")[0]['src']
    get_image(image_url, headers, cookies, artist['name'])

def curl_info():
    #prepair url, headers, cookies, and ids for requests
    ARTIST_PAGE_URL = "https://music.163.com/artist/desc"

    headers = {
        "referer": "https://music.163.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    }

    cookies = {
        "_iuqxldmzr_": "32",
        "*ntes*nnid": "66528d90a67b40f5083977b2aa13f1fb,1750984768492",
        "*ntes*nuid": "66528d90a67b40f5083977b2aa13f1fb",
        "WEVNSM": "1.0.0",
        "WNMCID": "wvtjxf.1750984768861.01.0",
        "NMTID": "00O7aLHpTbFcg_iC0nCm7NyqWczpIYAAAGXrtM58g",
        "sDeviceId": "YD-l%2B6BoGmhqc1AF1EQQQaTPoj4t09g4aiS",
        "ntes_utid": "tid._.mMP9FniabwxEBkRRUBeDP9jt8x8ksbiW._.0",
        "WM_TID": "%2BYEnlCDbZ1xFVUQQQQOCOoi8p04hzMbF",
        "**snaker**id": "CpNqIxmBogQLpWV9",
        "gdxidpyhxdE": "oC5cpwv7PdGK%5CrmjJB8pisHZ9m1bBCR4w4gVu%5C3l%5CdaVIcn1L9PMEOTPvc2C8cMYGtX4%2BX3N43UcZQ%2FC5xOL2zmMWV4Avj84tVTrpcwfbjN%2BLY31po577AjeOjXkfxxdf9fUWC9iWY1Ko9l9AVy3zsovRIhtL%2BVVzbY9dl0EYqvKTeab%3A1750985729881",
        "__csrf": "dd241c7029354383215c754cbca3fbbc",
        "MUSIC_U": "00C3F1F27B7227B3ADC8357A5221494AD43A2E473D70140C67E44C374292212270FD60D72117FF1C8D04F475CFC613AF28264AF280B916F00CA8541633CD8FF0DCA322F55A7545CBE45807FB36FABC2D8C9765E4835C0E517CC51EBA66B07B63B88377B4AB73DEA1792995652DEFDFA3A100511F345AFB8948D4847DCFE5063CAEF379ECC1C3EB07DD3EE103BC7F385C3BB0C1D4B47F8CFF3C0B8E1BFE0260AFC372679E42AA7A852234A6BC65C4309550185473C79DE4ADF8AA60605B73674309FA299BF95F163D527B4EB504389D48829AD480E1BD63652CF1EDA146C77FDADE91A513C8719F7E00FAAFD93519D6437CB0C52E7B519F95698A5FA5C7E5E4B32968C75C52F20F06B46D80ED1E25A0B02F56837B26D608822215B2C8A34A946CAB151832BA86D2F3B32BD196A4FCA46D1D9044C74CF5D9823C1098DB7EB73AC2ADED8A88FFACC861B2981645C2EF743FBE6747205EE9A20619C0AA1B44AD6C92C185DAB10053BD76255C9312E6D7D02B58",
        "__remember_me": "true",
        "P_INFO": "15652144978|1750984965|1|music|00&99|null&null&null#bej&null#10#0|&0||15652144978",
        "ntes_kaola_ad": "1",
        "JSESSIONID-WYYY": "XS7a6BigwtwhR0RhteE%2FVuxgGr1HyDUHnZATC8pH37RU6I1Su8sOXsrf33Adk7Y0bRTtjhcwtdZ%5CyG%2FcTdFoOxy%2Fza0JOFnsAfob3Hjw2hRx%2B4xyCW4iEZfzGfxAh3uIsoO%2BW0gKEiAru2uFdm6FBpKdwuniVD9ZYB%2BGd23DDpqXqoys%3A1751068190136",
        "WM_NI": "KaKg7wE4tYc7KsLvnkUbjDC0vBlN%2Bry9DP3%2B7O0osQKBQpX4wLoOA4r%2Bu%2BN9BICLyFdBTj0E1A%2BzViLHOjv9tEeD6WdfzVAunXOGebIELB2OeNdVX%2FHlzun8oRseYNnBQXU%3D",
        "WM_NIKE": "9ca17ae2e6ffcda170e2e6eed4b16f8c95fb96c54aae9a8fb7c44f829e9ab1d66af7b0aa8eeb4990ae009bd62af0fea7c3b92a89bf8588b67d87ecbcbae23d89ad8497ed6197bea6a5c23cb69ea4afaa7abbe78cb1b221f5910090f25b899e9f91db40b594a1b0c440b2f5bbcccd3382978dadfc4ea89e9c8bb34ff39fe59bd5639098818bf533b89baba5b55da8bab6b7c47fae8881a8e86a8b9b84a3b145a792acb7db258cb4b696ed34ad8ebd86dc46ae9e9fb9d837e2a3"
    }

    id_list = get_all_artist_ids()

    #curl all the artists
    for id in id_list:
        response = requests.get(url=ARTIST_PAGE_URL, headers=headers, cookies=cookies, 
                                params={"id": id})
        analyze_response(response, headers, cookies)
        time.sleep(random.random() + 1)
        

if __name__ == "__main__":
    curl_info()