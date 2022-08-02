import requests
import json
import stock_scraper
from dotenv import load_dotenv
import os

# initialization
load_dotenv()
base_url = "https://api.notion.com/v1/" # api base URL
token = os.environ.get('secretToken') # Notion token
database_id = os.environ.get('databaseId') # id of the Notion database
symbol_property_name = os.environ.get('symbolPropertyName') # name of the Notion database property for stock symbol
price_property_name = os.environ.get('pricePropertyName') # name of the Notion database property for stock price

# API header for authentication
headers = {
    "Accept": "application/json",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
    "Authorization": "Bearer " + token
}

# retrieve the property id of the properties to be read or updated within the database
database_retrieve_url = base_url + "databases/" + database_id
database_retrieve_response = requests.get(database_retrieve_url, headers=headers)
database_retrieve_response_json = database_retrieve_response.json() # convert response to json
symbol_property_id = database_retrieve_response_json["properties"][symbol_property_name]["id"]
price_property_id = database_retrieve_response_json["properties"][price_property_name]["id"]

# query the database and retrieve a list of all the pages inside
database_query_url = base_url + "databases/" + database_id + "/query"
database_query_response = requests.post(database_query_url, headers=headers)
database_query_response_json = database_query_response.json() # convert response to json

# loop through each page in the database
for page in database_query_response_json['results']:
    # retrieve the page id
    page_id = page['id']

    # read the symbol property of the page
    symbol_url = base_url + "pages/" + page_id + "/properties/" + symbol_property_id
    symbol_response = requests.get(symbol_url, headers=headers)
    symbol_response_json = symbol_response.json() # convert response to json
    symbol = symbol_response_json['results'][0]['rich_text']['plain_text']

    # read the existing value of the price property of the page
    price_url = base_url + "pages/" + page_id + "/properties/" + price_property_id
    price_response = requests.get(price_url, headers=headers)
    price_response_json = price_response.json() # convert response to json
    price_old = price_response_json['number']

    # retrieve the stock price of the symbol
    price_new = stock_scraper.get_stock_price(symbol)

    # update the price property of the page
    page_update_url = base_url + "pages/" + page_id
    page_update_payload = {"properties": {price_property_id: price_new}}
    page_update_response = requests.patch(page_update_url, json=page_update_payload, headers=headers)
    print(symbol+" price changed from "+str(price_old)+" to "+str(price_new))
