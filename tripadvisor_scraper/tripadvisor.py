import requests
from bs4 import BeautifulSoup
import concurrent.futures

base_url = "https://www.tripadvisor.com"

thread_pool_limit = 50      # It will use to give maximum retry of fail

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.54 Safari/537.36"
}

def scrap_uk_geo_from_url(args):
    url = args[0]
    geo_list = args[1]
    response = requests.get(url,headers=headers)
    bs_res = BeautifulSoup(response.text,"html.parser")

    print("url : ",url)
    get_all_links = bs_res.find_all("div",{"class":"geo_name"})
    if len(get_all_links) > 0:
        for link in get_all_links:
            geo_list.append(link.find("a")["href"].split("-")[1][1:])
    else:
        get_all_links = bs_res.find("ul",{"class":"geoList"}).find_all("a")
        for link in get_all_links:
            geo_list.append(link["href"].split("-")[1][1:])


def start_scrap_uk_geo():
    page = 0
    per_page_items = 20

    uk_cities_url = f"https://www.tripadvisor.com/Restaurants-g186216-oa{page}-United_Kingdom.html"
    response = requests.get(uk_cities_url,headers=headers)
    num_of_pages = int(response.text.split("numPages', '")[1].split("'")[0].strip())
    print("num_of_pages  : ",num_of_pages)

    geo_list = []

    with concurrent.futures.ThreadPoolExecutor(thread_pool_limit) as executor:
        while page < num_of_pages:
            uk_cities_url = f"https://www.tripadvisor.com/Restaurants-g186216-oa{page*per_page_items}-United_Kingdom.html"
            executor.submit(scrap_uk_geo_from_url,[uk_cities_url,geo_list])
            page += 1

    print("lent :: ", len(geo_list))

start_scrap_uk_geo()



# https://www.tripadvisor.com/RestaurantSearch?Action=PAGE&ajax=1&availSearchEnabled=true&sortOrder=popularity&geo=186338&o=a0
#
# https://www.tripadvisor.com/RestaurantSearch?Action=PAGE&ajax=1&availSearchEnabled=true&sortOrder=popularity&geo=186338&itags=10591&people=2&o=a30
#
# https://www.tripadvisor.com/RestaurantSearch?Action=PAGE&ajax=1&availSearchEnabled=true&sortOrder=popularity&geo=186338&itags=10591&people=2&o=a60