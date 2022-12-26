import amazon_page_analyser as apa

import random
import time

import telegram

def get_deals_urls():
    seleniumDriver = apa.start_selenium()
    deals_urls = apa.get_deals_urls(seleniumDriver)  #get deals only once
    seleniumDriver.quit()  #close everything that was created. Better not to keep driver open for much time
    return deals_urls

def get_random_product_info(deals_urls, used_products_ids):
    selected_url = random.choice(deals_urls)  # select a random product to get the info
    selected_product_info = apa.get_product_info(selected_url)

    while True:  # get new product until is the selected one is valid

        if(selected_product_info != None) and (selected_product_info["product_id"] not in used_products_ids):  #product valid and not already sent
            break

        deals_urls.remove(selected_url)  #remove url of invalid product
        selected_url = random.choice(deals_urls)
        selected_product_info = apa.get_product_info(random.choice(deals_urls))

    used_products_ids.append(selected_product_info["product_id"])

    if(len(used_products_ids) == 100):
        used_products_ids.pop(0)  #remove oldest product sent if enough time has passed

    return selected_product_info

def send_deal(bot, product_info, chat_id):

    emoticon = ['\U0000203C', '\U00002757', '\U0001F525', '\U000026A1']  #elements of message
    starting_text = ['A soli ', 'Solamente ', 'Soltanto ', 'Appena ']
    comparison_text = ['invece di ', 'al posto di ', 'piuttosto che ']


    caption = product_info["title"] + "\n\n"
    caption += "https://www.amazon.it/dp/" + product_info["product_id"] + "\n\n"
    caption += product_info["discount_rate"] + random.choice(emoticon) + "\n"
    caption += random.choice(starting_text) + product_info["new_price"] + ", " + random.choice(comparison_text) + product_info["old_price"] + random.choice(emoticon)

    bot.send_photo(chat_id, product_info["image_link"], caption)

if __name__ == '__main__':

    botToken = 'botTokenHere'
    bot = telegram.Bot(token=botToken)

    used_products_ids = []
    deals_urls = get_deals_urls()

    channel_id = '@channelNameHere'
    start = time.time()

    while(True):

        if(time.localtime().tm_hour > 22 or time.localtime().tm_hour < 8):  #do not send messages during the nigth
            time.sleep(3600)
            continue

        if(time.time() - start > 2*3600):
            deals_urls = get_deals_urls()
            start = time.time()

        selected_product_info = get_random_product_info(deals_urls, used_products_ids)
        send_deal(bot, selected_product_info, channel_id)

        time.sleep(random.randrange(60 * 20, 60 * 30))  # send every 20 to 30 minutes
