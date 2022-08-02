import requests
from bs4 import BeautifulSoup

yahoo_finance_base_url = "https://finance.yahoo.com/quote/"

# takes a stock symbol and find the current price on Yahoo Finance
def get_stock_price(symbol):
    stock_url = yahoo_finance_base_url + symbol # the URL of the stock page on Yahoo Finance
    webpage_response = requests.get(stock_url) 
    webpage_doc = BeautifulSoup(webpage_response.text, 'html.parser') # parse the content from the webpage
    price_tag = webpage_doc.find('fin-streamer', {'class': "Fw(b) Fz(36px) Mb(-4px) D(ib)"}) # extract the html tag containing the stock price
    price = float(price_tag.text)
    return price