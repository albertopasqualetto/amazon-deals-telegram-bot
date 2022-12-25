from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

import re


def start_selenium():
	chrome_options = Options()
	chrome_options.add_argument("--headless")
	# driver = webdriver.Chrome(options=chrome_options)
	# driver = webdriver.Edge(service=EdgeService(executable_path="../msedgedriver.exe"), options=chrome_options)
	driver = webdriver.Remote(
		command_executor='http://129.152.19.184:80/wd/hub',
		options=chrome_options
	)
	return driver


def get_elements(selenium, page_url):
	try:
		selenium.get(page_url)
		selenium.execute_script("arguments[0].click();", selenium.find_element(By.LINK_TEXT, "Sconto del 50% o più"))
		elements_urls = [e.get_attribute("href") for e in
		                 selenium.find_elements(By.CSS_SELECTOR, "a[class*='DealCard']")]
		print(elements_urls[0])
		return elements_urls

	# except Exception as E:

	finally:
		selenium.close()


def is_product(url):
	return "/dp/" in url


def get_products_from_links(links):
	products = []
	for link in links:
		if is_product(link):
			products.append(link)
	return products

def get_product_info(selenium, product_url):
	selenium.get(product_url)
	product_id = re.search('dp\/(.+?)\?', product_url).group(1)
	title = selenium.find_element(By.CSS_SELECTOR, "span[id='productTitle']")
	old_price = selenium.find_element(By.CSS_SELECTOR, "span[class='a-price'] span[data-a-strike='true'] span[class='a-offscreen']")
	new_price = selenium.find_element(By.CSS_SELECTOR, "span[class='a-price'] span[class$='apexPriceToPay'] span[class='a-offscreen']")
	discount_rate = selenium.find_element(By.CSS_SELECTOR, "span[class='a-color-price']")

	return {
		"product_id" : product_id,
		"title" : title,
		"old_price" : old_price,
		"new_price" : new_price,
		"discount_rate" : discount_rate
	}