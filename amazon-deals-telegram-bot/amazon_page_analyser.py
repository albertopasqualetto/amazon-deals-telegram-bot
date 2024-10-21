from selenium import webdriver

from selenium.webdriver.common.by import By  # get element by

from selenium.webdriver.support.wait import WebDriverWait  # wait for the 50% deals page to load
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

import re  # use regex for selecting product id in link

import time # wait for dynamic deals to load
import random # use random user agent to avoid scrape blocking

import requests  # lighter way to retrieve information from html only (no js and css loaded)
from lxml import html

from babel.numbers import parse_decimal  # from price to number

import os

def start_selenium():
    chromium_service = Service()  # now Selenium download the correct version of the webdriver

    chromium_options = webdriver.ChromeOptions()  # add the debug options you need
    chromium_options.add_argument("--headless")  # do not open chromium gui
    chromium_options.add_argument('--log-level=1') # remove useless logs

    # create a Chromium tab with the selected options
    chromium_driver = webdriver.Chrome(service=chromium_service, options=chromium_options)

    return chromium_driver


def get_all_deals_ids():
    deals_page = f"https://www.amazon.{os.environ.get("AMAZON_COUNTRY_TLD")}/{os.environ.get("AMAZON_DEALS_SUBPAGE")}/"
    selenium_driver = start_selenium()

    print("Starting taking all urls")

    try:
        selenium_driver.get(deals_page)

        # go to page with 50% or more deals (the radio with value 3)
        deals_50_button = selenium_driver.find_element(By.XPATH, '//input[@type="radio" and @name="percentOff" and @value="3"]')
        selenium_driver.execute_script("arguments[0].click();", deals_50_button)

        # when the page with the deals above 50% loads, the deals become clickable.
        # Checking for document.readyState would not work (is already ready, just loads different deals)
        # Checking for url change would not work, because it changes before the new deals are loaded
        WebDriverWait(selenium_driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='product-card']")))  # timeout connect after 60 seconds

        elements_urls = []
        # scroll the page little by little to load more deals. Take the deals present after each scroll
        for _ in range(100):
            selenium_driver.execute_script("window.scrollBy(0, 200);")

            time.sleep(0.2)

            # get all urls from <a> tags under <div> tags that contain "data-testid='product-card'". There are both immediate deals and submenus with deals
            elements_urls += [e.find_element(By.TAG_NAME, 'a').get_attribute("href") for e in
                            selenium_driver.find_elements(By.CSS_SELECTOR, "[data-testid='product-card']")]

        deals_urls = []  # store all deals urls from main page and from submenus
        for url in elements_urls:
            if is_product(url):
                deals_urls.append(url)
            if ('/deal/' in url) or ('/browse/' in url):  # if an url leads to a submenu
                deals_urls = deals_urls + get_submenus_urls(url)  # add the deals from submenus

        print("All urls taken. Extracting the ids")

        # keep only product ids because they can be easily used to create the link for that product
        product_ids = [extract_product_id(url) for url in deals_urls if
                       extract_product_id(url) is not None and extract_product_id(url) != '']

        selenium_driver.quit()  # close everything that was created. Better not to keep driver open for much time
        return [*set(product_ids)]  # remove duplicates

    except Exception as e:
        print(e)
        selenium_driver.quit()  # close everything that was created. Better not to keep driver open for much time
        return []  # error, no ids taken


def get_submenus_urls(submenu_url):
    # headers needed to avoid scraping blocking
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.1 Safari/605.1.15', }
    submenu_page = requests.get(submenu_url, headers=headers)
    submenu_page_content = html.fromstring(submenu_page.content)

    # only deals which are present if cookies are not accepted (no suggestions at the bottom of the page)
    elements_urls = submenu_page_content.xpath('//a[contains(@class, "a-link-normal")]/@href')

    return [x for x in elements_urls if is_product(x)]  # remove all urls that are not deals (for example, share urls)


def is_product(url):  # products have /dp/ in their url
    return "/dp/" in url


def extract_product_id(url):
    try:
        # using regex, get the id, that is what follows "dp/" and that comes before "/" or "?"
        return re.search('dp\/(.*?)(?=\/|\?)', url).group(1)
    except:
        return None


def url_from_id(product_id):
    return "https://www.amazon.it/dp/" + product_id


def get_product_info(product_id, remove_ebooks=False):
    # headers needed to avoid scraping blocking (helps at least a bit)
    user_agents = [
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
    ]

    headers = {'User-Agent': random.choice(user_agents)}

    params = {
        'th': '1',
        'psc': '1'
    }  # using params to not waste links where there are variants
    product_page = requests.get(url_from_id(product_id), headers=headers, params=params)  # necessary to use get and not post when using params

    product_page_content = html.fromstring(product_page.content)

    try:
        # elements may not be found if the deal is a subscription (regular purchase)
        title = product_page_content.xpath('//span[@id="productTitle"]/text()')[0].strip()

        # the product is not an ebook
        if(len(product_page_content.xpath('//*[@id="kindle-price"]')) == 0):

            old_price = product_page_content.xpath('//span[@data-a-strike="true"]//span[@aria-hidden="true"]/text()')[0]

            # translate() to make case-insensitive (class may be priceToPay or apexPriceToPay)
            new_price = product_page_content.xpath('//span[contains(translate(@class, "PRICETOPAY", "pricetopay"), "pricetopay")]//span[@class="a-offscreen"]/text()')[0]

            if(new_price == ' '):  # there is another way the price may be displayed (whole and decimal part)
                new_price_whole = product_page_content.xpath('//span[contains(translate(@class, "PRICETOPAY", "pricetopay"), "pricetopay")]//span[@aria-hidden="true"]//span[@class="a-price-whole"]/text()')[0]
                new_price_decimal = product_page_content.xpath('//span[contains(translate(@class, "PRICETOPAY", "pricetopay"), "pricetopay")]//span[@aria-hidden="true"]//span[@class="a-price-fraction"]/text()')[0]
                new_price = new_price_whole + ',' + new_price_decimal + '€'  # put it in the other format, to use the same formula

        elif(not remove_ebooks):
            # the price is written a bit differently, so:
            # remove the last two characters
            # remove any useless white space
            # add again the euro sign
            old_price = product_page_content.xpath('//*[@id="basis-price"]/text()')[0][:-2].strip() + "€"
            new_price = product_page_content.xpath('//*[@id="kindle-price"]/text()')[0][:-2].strip() + "€"
        
        else:
            print("Skipping ebook")
            return None  # ignore the ebook

        # calculate discount rate from new and old prices. Round to int and add '-' and '%' signs
        discount_rate = "-" + str(round(100 - (parse_decimal(new_price.strip('€'), locale='it') / parse_decimal(old_price.strip('€'), locale='it')) * 100)) + "%"

        image = product_page_content.xpath('//img[@id="landingImage"]/@src')

        if(len(image) == 0): # there is another way an image may be displayed
            image = product_page_content.xpath('//div[contains(@class, "a-dynamic-image-container")]//img/@src')

        image_link = image[0].split("._")[0] + ".jpg"  # remove latter part of image link to get the highest resolution

        return {
            "product_id": product_id,
            "title": title,
            "old_price": old_price,
            "new_price": new_price,
            "discount_rate": discount_rate,
            "image_link": image_link
        }

    except Exception as e:
        print("\nError for product id:\n\n" + product_id + "\n\nbecause:\n\n" + str(e) + "\nProbably strange formatting of webpage.\n")
        return None
