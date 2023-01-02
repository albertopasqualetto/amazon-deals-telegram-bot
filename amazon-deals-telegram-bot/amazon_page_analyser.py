from selenium import webdriver

from selenium.webdriver.common.by import By  # get element by

from selenium.webdriver.support.wait import WebDriverWait  # wait for the 50% deals page to load
from selenium.webdriver.support import expected_conditions as EC

import re  # use regex for selecting product id in link

import requests  # lighter way to retrieve information from html only (no js and css loaded)
from lxml import html


def start_selenium(webdriver_path):
    chromium_options = webdriver.ChromeOptions()  # add the debug options you need
    chromium_options.add_argument("--headless")  # do not open chromium gui
    chromium_options.add_argument('--disable-gpu')  # disable hardware acceleration for compatibility reasons

    # create a Chromium tab with the selected options
    chromium_driver = webdriver.Chrome(executable_path=webdriver_path, options=chromium_options)

    return chromium_driver


def get_all_deals_ids(webdriver_path):
    deals_page = "https://www.amazon.it/deals/"
    selenium_driver = start_selenium(webdriver_path)

    print("Starting taking all urls")

    try:
        selenium_driver.get(deals_page)

        # go to page with 50% or more deals
        selenium_driver.execute_script("arguments[0].click();",
                                       selenium_driver.find_element(By.PARTIAL_LINK_TEXT,
                                                                    "Sconto del 50%"))  # not using full text to avoid problems with utf-8

        # when the page with the deals above 50% loads, the deals become clickable.
        # Checking for document.readyState would not work (is already ready, just loads different deals)
        # Checking for url change would not work, because it changes before the new deals are loaded
        WebDriverWait(selenium_driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[class*='DealCard']")))  # timeout connect after 60 seconds

        # get all urls with <a> tag with a css class that contains 'DealCard'. There are both immediate deals and submenus with deals
        elements_urls = [e.get_attribute("href") for e in
                         selenium_driver.find_elements(By.CSS_SELECTOR, "a[class*='DealCard']")]

        deals_urls = []  # store all deals urls from main page and from submenus
        for url in elements_urls:
            if is_product(url):
                deals_urls.append(url)
            if ('/deal/' in url) or ('/browse/' in url):  # if an url leads to a submenu
                deals_urls = deals_urls + get_submenus_urls(url)  # add the deals from submenus

        print("All urls taken. Extracting the ids")

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
    return re.search('dp\/(.*?)(?=\/|\?)', url).group(1)


def url_from_id(product_id):
    return "https://www.amazon.it/dp/" + product_id


def get_product_info(product_id):
    # headers needed to avoid scraping blocking
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0', }
    params = {
        'th': '1',
        'psc': '1'
    }  # using params to not waste links where there are variants TODO
    product_page = requests.get(url_from_id(product_id), headers=headers, params=params)  # necessary to use get and not post when using params

    product_page_content = html.fromstring(product_page.content)

    try:
        # elements may not be found if the deal has variants (page has only price range) TODO (only leave subscriptions not valid)
        title = product_page_content.xpath('//span[@id="productTitle"]/text()')[0].strip()
        old_price = product_page_content.xpath('//span[@data-a-strike="true"]//span[@aria-hidden="true"]/text()')[0]
        new_price = product_page_content.xpath('//span[contains(@class, "priceToPay")]//span[@class="a-offscreen"]/text()')[0]
        discount_rate = product_page_content.xpath('//span[contains(@class, "savingsPercentage")]/text()')[0]
        image_link = product_page_content.xpath('//img[@id="landingImage"]/@src')[0].split("._")[0] + ".jpg"  # remove latter part of image link to get the highest resolution

        return {
            "product_id": product_id,
            "title": title,
            "old_price": old_price,
            "new_price": new_price,
            "discount_rate": discount_rate,
            "image_link": image_link
        }

    except Exception as e:
        print("\nError for product id:\n\n" + product_id + "\n\nbecause:\n\n" + str(e) + "\n Probably strange formatting of webpage.\n")
        return None
