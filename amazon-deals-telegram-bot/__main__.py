import amazon_page

starting_page = "https://www.amazon.it/blackfriday/"

if __name__ == '__main__':
	selenium = amazon_page.start_selenium()
	amazon_page.get_elements(selenium, starting_page)