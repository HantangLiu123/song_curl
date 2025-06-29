import requests
from bs4 import BeautifulSoup
import re
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from artist_info_curl import get_all_artist_ids
from requests_get import RequestsGet
from store import ARTIST_SONG_IDS_PATH, SONG_IMAGE_PATH, SONG_INTRO_PATH

def construct_song_id_list(song_url_list: list[str]) -> list[int]:
    
    """function that constructs songs' id list from their urls"""
    
    id_list = []
    for url in song_url_list:
        _, id = re.split(r'=', url, maxsplit=1)
        id_list.append(int(id))
    return id_list

def get_songs_info(tool: RequestsGet, driver: webdriver.Chrome, song_url_list: list[str]):
    #preventing same song appear twice
    song_id_set = set()
    for url in song_url_list:
        song_info = {}

        #getting the id from the url
        _, song_id = re.split(r'=', url, maxsplit=1)
        if song_id in song_id_set:
            continue
        song_id_set.add(song_id)
        song_info['id'] = song_id
        song_info['url'] = f"https://music.163.com{url}"

        #getting song name, artists information from requests
        response = tool.requests_get(song_info['url'])
        response.raise_for_status()
        song_soup = BeautifulSoup(response.text, 'lxml')

        #find the song name and alias
        song_title = song_soup.title
        if re.search(r'（.+）', song_title.text) is not None:
            song_info['name'] = re.split(r'（', song_title.text, maxsplit=1)[0].strip()
            song_alias = re.search(r'（.+）', song_title.text)
            song_alias = song_alias.group(0)
            song_info['alias'] = song_alias[1:len(song_alias) - 1]
        else:
            song_info['name'] = re.split(r'-', song_title.text)[0].strip()

        #artists' names and ids
        artist_tags = song_soup.find_all(href=re.compile(r'^/artist\?id=[0-9]+$'), class_="s-fc7")
        artist_list = []
        artist_id_list = []
        for tag in artist_tags:
            artist_list.append(tag.text)
            artist_href = tag['href']
            _, artist_id = re.split(r'=', artist_href, maxsplit=1)
            artist_id_list.append(artist_id)
        song_info['artist list'] = artist_list
        song_info['artist id list'] = artist_id_list

        #getting the lyrics and picture with webdriver
        driver.get(song_info['url'])
        wait = WebDriverWait(driver, 15) #driver will wait for at most 15s for any movement or raise errors

        #change to iframe 
        iframe = wait.until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
        driver.switch_to.frame(iframe)

        #get the image
        image = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'j-img')))
        img_url = image.get_attribute('src')
        IMG_PATH = f'{SONG_IMAGE_PATH}/song{song_id}.jpg'
        response = requests.get(img_url, stream=True)
        with open(IMG_PATH, "wb") as f:
            for chunck in response.iter_content(chunk_size=8192):
                f.write(chunck)
        print(f"song{song_id}'s image saved")

        #click the "展开" button for lyrics
        try:
            more = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()='展开']")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", more)
            time.sleep(0.5)
            more.click()
        except TimeoutException:
            print('No "展开" button')
        
        #get the lyrcis
        element = driver.find_element(By.ID, "lyric-content")
        lyrics = element.text
        song_info['lyrics'] = lyrics

        #store the song
        INTRO_PATH = f"{SONG_INTRO_PATH}/song{song_id}.json"
        with open(INTRO_PATH, 'w', encoding='utf-8') as f:
            json.dump(song_info, f, ensure_ascii=False, sort_keys=False, indent=4)
        print(f"song{song_id}'s intro is saved")

def curl_song_through_artists(tool: RequestsGet, driver: webdriver.Chrome):

    """a function getting songs from known artists"""

    ARTIST_SONGPAGE_URL = "https://music.163.com/artist"
    artist_id_list = get_all_artist_ids()
    flag = False
    for id in artist_id_list:

        #get the artist's songs page
        response = tool.requests_get(url=ARTIST_SONGPAGE_URL, params={'id': id})
        response.raise_for_status()
        song_list_soup = BeautifulSoup(response.text, 'lxml')
        song_list = song_list_soup.find("ul", class_="f-hide")
        song_url_list = [song.a['href'] for song in song_list]
        #get first 25 songs
        song_url_list = song_url_list[:25]

        #get the id list and stores
        song_id_list = construct_song_id_list(song_url_list)
        STORE_PATH = f'{ARTIST_SONG_IDS_PATH}/artist{id}songs.json'
        with open(STORE_PATH, "w", encoding='utf-8') as f:
            json.dump(song_id_list, f, sort_keys=False, indent=4)
        print(f"artist{id}'s songs' ids saved")
        
        #get and store the songs info
        get_songs_info(tool, driver, song_url_list)

if __name__ == "__main__":
    #prepare for requests
    tool = RequestsGet(
        headers = {
            "referer": "https://music.163.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
        }, 
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
    )
    
    #prepare selenium driver without screen
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--enable-javascript')
    driver = webdriver.Chrome(options=chrome_options)

    curl_song_through_artists(tool, driver)
    driver.quit()
