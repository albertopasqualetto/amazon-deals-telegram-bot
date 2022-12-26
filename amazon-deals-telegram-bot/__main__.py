import amazon_page_analyser as apa

import random
import time

import telegram


def get_deals():
    selenium_driver = apa.start_selenium()
    deals_ids = apa.get_deals_ids(selenium_driver)  # get deals only once
    selenium_driver.quit()  # close everything that was created. Better not to keep driver open for much time
    return deals_ids


def get_random_product_info(deals_ids, already_sent_products_ids):
    selected_deal_id = random.choice(deals_ids)  # select a random product to get the info
    selected_product_info = apa.get_product_info(selected_deal_id)

    while True:  # get new product until the selected one is valid
        if (selected_product_info is not None) and (
                selected_product_info[
                    "product_id"] not in already_sent_products_ids):  # product valid and not already sent
            break

        deals_ids.remove(selected_deal_id)  # remove already used product
        selected_deal_id = random.choice(deals_ids)
        selected_product_info = apa.get_product_info(random.choice(deals_ids))

    already_sent_products_ids.append(selected_product_info["product_id"])
    # it is necessary to save used products ids and not remove them from the list because the list is recreated every few hours

    if len(already_sent_products_ids) == 100:
        already_sent_products_ids.pop(0)  # remove the oldest product sent if enough time has passed

    return selected_product_info


def send_deal(bot, product_info, chat_id):
    emoticon = ['\U0000203C', '\U00002757', '\U0001F525', '\U000026A1']  # elements of message
    starting_text = ['A soli ', 'Solamente ', 'Soltanto ', 'Appena ']
    comparison_text = ['invece di ', 'al posto di ', 'piuttosto che ']

    caption = product_info["title"] + "\n\n"
    caption += "https://www.amazon.it/dp/" + product_info["product_id"] + "\n\n"  # add affiliate code here
    caption += product_info["discount_rate"] + random.choice(emoticon) + "\n"
    caption += random.choice(starting_text) + product_info["new_price"] + ", " + random.choice(comparison_text) + \
               product_info["old_price"] + random.choice(emoticon)

    bot.send_photo(chat_id, product_info["image_link"], caption)


if __name__ == '__main__':

    botToken = 'botTokenHere'
    bot = telegram.Bot(token=botToken)

    already_sent_product_ids = []
    deals_ids = get_deals()

    channel_id = '@channelNameHere'
    start = time.time()

    while True:

        if time.localtime().tm_hour > 22 or time.localtime().tm_hour < 8:  # do not send messages during the night
            time.sleep(3600)
            continue

        if time.time() - start > 2 * 3600:  # updated deals every 2 hours
            deals = get_deals()
            start = time.time()

        selected_product_info = get_random_product_info(deals_ids, already_sent_product_ids)
        send_deal(bot, selected_product_info, channel_id)

        time.sleep(random.randrange(60 * 20, 60 * 30))  # send every 20 to 30 minutes
