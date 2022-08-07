import requests
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup

# initialization
load_dotenv() # read the .env file
yahoo_finance_base_url = "https://finance.yahoo.com/quote/"
notion_base_url = "https://api.notion.com/v1/" # Notion API base URL
token = os.environ.get('secretToken') # Notion token
database_id = os.environ.get('databaseId') # id of the Notion database
symbol_property_name = os.environ.get('symbolPropertyName') # name of the Notion database property for stock symbol
price_property_name = os.environ.get('pricePropertyName') # name of the Notion database property for stock price
price_target_property_name = os.environ.get('priceTargetPropertyName') # name of the Notion database property for stock price target
type_property_name = os.environ.get('typePropertyName') # name of the Notion database property for asset type

# Notion API header for authentication
notion_headers = {
    "Accept": "application/json",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
    "Authorization": "Bearer " + token
}

# header to pretend the request actually comes from a browser when scraping webpages
scrape_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
}

# retrieve the property id of the properties to be read or updated within the database
database_retrieve_url = notion_base_url + "databases/" + database_id
database_retrieve_response = requests.get(database_retrieve_url, headers=notion_headers)
database_retrieve_response_json = database_retrieve_response.json() # convert response to json
symbol_property_id = database_retrieve_response_json["properties"][symbol_property_name]["id"]
price_property_id = database_retrieve_response_json["properties"][price_property_name]["id"]
price_target_property_id = database_retrieve_response_json["properties"][price_target_property_name]["id"]
type_property_id = database_retrieve_response_json["properties"][type_property_name]["id"]

# query the database and retrieve a list of all the pages inside that represent stocks
# filtered by Type = Stock
# sorted by stock symbol
database_query_url = notion_base_url + "databases/" + database_id + "/query"
database_query_payload = {
    "filter": {
        "property": type_property_name, 
        "select": {
            "equals": "Stock"
        }
    }, 
    "sorts": [
        {
            "property": symbol_property_name, 
            "direction": "ascending"
        }
    ]
}
database_query_response = requests.post(database_query_url, json = database_query_payload, headers=notion_headers)
database_query_response_json = database_query_response.json() # convert response to json

# loop through each stock page in the database
count = 0
for page in database_query_response_json['results']:
    # retrieve the page id
    page_id = page['id']

    # read the symbol property of the page
    symbol_url = notion_base_url + "pages/" + page_id + "/properties/" + symbol_property_id
    symbol_response = requests.get(symbol_url, headers=notion_headers)
    symbol_response_json = symbol_response.json() # convert response to json
    # skip this page if the symbol property is empty
    if(len(symbol_response_json['results']) == 0):
        continue
    symbol = symbol_response_json['results'][0]['rich_text']['plain_text']

    # connect to the stock webpage on Yahoo Finance and parse the content
    stock_url = yahoo_finance_base_url + symbol # the URL of the stock page on Yahoo Finance
    webpage_response = requests.get(stock_url, headers=scrape_headers)
    # skip this page if the webpage corresponding to the symbol does not exist
    if (webpage_response.status_code != 200):
        print(symbol+": Error: symbol is incorrect. " + stock_url)
        continue
    webpage_doc = BeautifulSoup(webpage_response.text, 'html.parser') # parse the content from the webpage
    
    # get the current stock price
    price_tag = webpage_doc.find('fin-streamer', {'class': "Fw(b) Fz(36px) Mb(-4px) D(ib)"}) # extract the html tag containing the stock price
    price_new = float(price_tag.text)

    # get the current average stock price target (if available)
    price_target_tag = webpage_doc.find('td', {'class': "Ta(end) Fw(600) Lh(14px)", 'data-test': "ONE_YEAR_TARGET_PRICE-value"}) # extract the html tag containing the stock price target
    try:
        price_target_new = float(price_target_tag.text) 
    except:
        price_target_new = None # return empty if the price target is not available

    # read the existing value of the price property of the page
    price_url = notion_base_url + "pages/" + page_id + "/properties/" + price_property_id
    price_response = requests.get(price_url, headers=notion_headers)
    price_response_json = price_response.json() # convert response to json
    price_old = price_response_json['number']

    # read the existing value of the price target property of the page
    price_target_url = notion_base_url + "pages/" + page_id + "/properties/" + price_target_property_id
    price_target_response = requests.get(price_target_url, headers=notion_headers)
    price_target_response_json = price_target_response.json() # convert response to json
    price_target_old = price_target_response_json['number']

    # update the price property of the page
    page_update_url = notion_base_url + "pages/" + page_id
    page_update_payload = {
        "properties": {
            price_property_id: price_new, 
            price_target_property_id: price_target_new
        }
    }
    page_update_response = requests.patch(page_update_url, json=page_update_payload, headers=notion_headers)
    print(
        symbol+": price changed from "+str(price_old)+" to "+str(price_new)+
        ", price target changed from "+str(price_target_old)+" to "+str(price_target_new)
    )
    count += 1

print("Updated "+ str(count) + " pages.")
