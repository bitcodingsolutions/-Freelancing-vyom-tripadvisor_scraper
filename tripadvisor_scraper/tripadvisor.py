import json
import math

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

    # print("url : ",url)
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

    print("len :: ", len(geo_list))
    return geo_list


# ---------------------------------------------------------------------------------------------

def scrap_hotel_reviews_from_url(args):
    url = args[0]
    hotel_reviews = args[1]

    response = requests.get(url,headers=headers)
    bs_res = BeautifulSoup(response.text,"html.parser")

    reviews_tag = bs_res.find_all("div", {"class":"rev_wrap ui_columns is-multiline"})

    for review_tag in reviews_tag:
        print(review_tag)

    print("BS : ",bs_res)

def scrap_hotel_reviews(args):
    url = args[0]
    num_of_reviews = args[1]

    hotel_reviews = []

    page = 0
    per_page_items = 10
    num_of_pages = math.floor(int(num_of_reviews)/per_page_items)
    with concurrent.futures.ThreadPoolExecutor(thread_pool_limit) as executor:
        while page <= num_of_pages:
            review_url = url.replace("Reviews-",f"Reviews-or{page*per_page_items}-")
            executor.submit(scrap_hotel_reviews_from_url,[review_url,hotel_reviews])
            page += 1
    return hotel_reviews


def scrap_hotel_details_from_url(args):
    url = args[0]
    hotel_details = args[1]

    restaurant = {}

    response = requests.get(url,headers=headers)

    try:
        json_str = response.text.split("window.__WEB_CONTEXT__={pageManifest:")[1].split("};")[0]
        json_data = json.loads(json_str)

        restaurants_obj = None
        for key in json_data['redux']['api']['responses']:
            if "/data/1.0/location" in key and "/hours" not in key:
                restaurants_obj = json_data['redux']['api']['responses'][key]
                print(key," : restaurants_obj : ",restaurants_obj)
                break

        restaurants_overview_obj = None
        for key in json_data['redux']['api']['responses']:
            if "/overview" in key:
                restaurants_overview_obj = json_data['redux']['api']['responses'][key]
                print(key," : restaurants_overview_obj : ",restaurants_overview_obj)
                break

        restaurant['name'] = restaurants_obj["data"]["name"]
        restaurant['website'] = restaurants_obj["data"]["website"]
        restaurant['rating'] = restaurants_obj["data"]["rating"]
        restaurant['num_reviews'] = restaurants_obj["data"]["num_reviews"]
        restaurant['full_address'] = restaurants_obj["data"]["address"]
        restaurant['street'] = restaurants_obj["data"]["address_obj"]["street1"]
        if restaurants_obj["data"]["address_obj"]["street2"]:
            restaurant['street'] += "," + restaurants_obj["data"]["address_obj"]["street2"]
        restaurant['city'] = restaurants_obj["data"]["address_obj"]["city"]
        restaurant['state'] = restaurants_obj["data"]["address_obj"]["state"]
        restaurant['country'] = restaurants_obj["data"]["address_obj"]["country"]
        restaurant['postal_code'] = restaurants_obj["data"]["address_obj"]["postalcode"]
        restaurant['cuisine'] = ""
        for item in restaurants_overview_obj['data']['detailCard']['tagTexts']['cuisines']["tags"]:
            restaurant['cuisine'] += item["tagValue"]+", "
        if restaurant['cuisine']:
            restaurant['cuisine'] = restaurant['cuisine'].strip()[:-1]

        restaurant['special_diets'] = ""
        for item in restaurants_overview_obj['data']['detailCard']['tagTexts']['dietaryRestrictions']["tags"]:
            restaurant['special_diets'] += item["tagValue"]+", "
        if restaurant['special_diets']:
            restaurant['special_diets'] = restaurant['special_diets'].strip()[:-1]

        restaurant['is_claimed'] = json_data["features"]["restaurants_claimed_badge"]
        restaurant['rating_questions'] = restaurants_overview_obj['data']["rating"]["ratingQuestions"]
        restaurant['reviews'] = scrap_hotel_reviews([url,restaurant['num_reviews']])

        hotel_details.append(restaurant)
    except Exception as e:
        print("Exception : ",e)


def scrap_geo_hotels_from_url(args):
    url = args[0]
    hotels_list = args[1]

    response = requests.get(url,headers=headers)
    bs_res = BeautifulSoup(response.text,"html.parser")

    # print("url : ",url)
    get_all_links = bs_res.find_all("a",{"class":"bHGqj Cj b"})

    with concurrent.futures.ThreadPoolExecutor(thread_pool_limit) as executor:
        for link in get_all_links:
            hotel_url = base_url+link["href"]
            executor.submit(scrap_hotel_details_from_url,[hotel_url,hotels_list])
            # break


def start_scrap_geo_hotels():
    # geo_list = start_scrap_uk_geo()
    geo_list = ["186338"]

    hotels_list = []

    for geo_item in geo_list:
        page = 0
        per_page_items = 30
        geo_hotels_url = f"https://www.tripadvisor.com/RestaurantSearch?Action=PAGE&ajax=1&availSearchEnabled=true&sortOrder=popularity&geo={geo_item}&o=a0"
        response = requests.get(geo_hotels_url,headers=headers)
        # print("geo_hotels_url : ",geo_hotels_url)
        num_of_pages = int(response.text.split("numPages', '")[1].split("'")[0].strip())
        print("num_of_pages  : ",num_of_pages)

        with concurrent.futures.ThreadPoolExecutor(thread_pool_limit) as executor:
            while page < num_of_pages:
                geo_hotels_url = f"https://www.tripadvisor.com/RestaurantSearch?Action=PAGE&ajax=1&availSearchEnabled=true&sortOrder=popularity&geo={geo_item}&o=a{page*per_page_items}"
                # print("geo_hotels_url : ",geo_hotels_url)
                executor.submit(scrap_geo_hotels_from_url,[geo_hotels_url,hotels_list])
                page += 1
                break
        break

    print("hotel len :: ", len(hotels_list))
    return hotels_list

start_scrap_geo_hotels()
