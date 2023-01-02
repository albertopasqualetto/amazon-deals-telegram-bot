import amazon_page_analyser as apa

import random
import time

from dotenv import dotenv_values

import telegram

import json


def get_random_product_info(deals_ids, already_sent_products_ids):
    if(len(deals_ids) == 0):
        return None

    selected_deal_id = random.choice(deals_ids)  # select a random product to get the info
    selected_product_info = apa.get_product_info(selected_deal_id)

    while True:  # get new product until the selected one is valid
        if (selected_product_info is not None) and (
                selected_product_info[
                    "product_id"] not in already_sent_products_ids):  # product valid and not already sent
            break

        deals_ids.remove(selected_deal_id)  # remove invalid product

        if(len(deals_ids) == 0):  # avoid infinte loop if there are no more products
            return None

        selected_deal_id = random.choice(deals_ids)
        selected_product_info = apa.get_product_info(random.choice(deals_ids))

    already_sent_products_ids.append(selected_product_info["product_id"])
    # it is necessary to save used products ids and not only remove them from the list because the list is recreated every few hours

    if len(already_sent_products_ids) == 100:
        already_sent_products_ids.pop(0)  # remove the oldest product sent if enough time has passed

    return selected_product_info


def send_deal(bot, product_info, chat_id):
    if(product_info == None):
        return

    emoticon = ['\U0000203C', '\U00002757', '\U0001F525', '\U000026A1', '\U00002728']  # elements of message
    starting_text = ['A soli ', 'Solamente ', 'Soltanto ', 'Appena ', 'Incredibilmente solo ', 'Incredibilmente soltanto ']
    comparison_text = ['invece di ', 'al posto di ', 'piuttosto che ']

    caption = product_info["title"] + "\n\n"
    caption += apa.url_from_id(product_info["product_id"]) + "\n\n"  # add affiliate code here
    caption += product_info["discount_rate"] + random.choice(emoticon) + "\n"
    caption += random.choice(starting_text) + product_info["new_price"] + ", " + random.choice(comparison_text) + \
               product_info["old_price"] + random.choice(emoticon)

    print("\nMessage sent:\n" + caption + "\n")

    bot.send_photo(chat_id, product_info["image_link"], caption)

# This script is executed every time a new message needs to be sent. For this reason it is necessary to save
# Data in a json file to avoid scraping every time the deals, and to avoid sending the same deals back to back.
# An alternative would be to have a while loop with a delay, but it would not be optimised for cron.
if __name__ == '__main__':

    config = dotenv_values(".env")  # TODO it may be better using environment variables if using containers

    new_collection_time = None
    already_sent_product_ids = []

    # if json exist
    try:

        with open("deals_ids.json", "r") as file:

            deals_dict = json.load(file)
            deals_ids = deals_dict["deals_ids"]
            already_sent_product_ids = deals_dict["already_sent_product_ids"]
            if time.time() - float(deals_dict["collection_time"]) > 2*3600:     # update deals every 2 hours
                deals_ids = apa.get_all_deals_ids()
                new_collection_time = time.time()

    except OSError as e:
        deals_ids = apa.get_all_deals_ids()
        new_collection_time = time.time()

    bot = telegram.Bot(token=config["AMAZON_DEALS_TG_BOT_TOKEN"])

    selected_product_info = get_random_product_info(deals_ids, already_sent_product_ids)
    send_deal(bot, selected_product_info, config["AMAZON_DEALS_TG_CHANNEL_ID"])

    # save deals collection time, the ids of new deals and the ids of the already sent products in a json file
    deals_dict = {"collection_time": new_collection_time if new_collection_time else deals_ids["collection_time"],
                  "deals_ids": deals_ids,
                  "already_sent_product_ids": already_sent_product_ids}
    with open("deals_ids.json", "w") as file:
        json.dump(deals_dict, file)
