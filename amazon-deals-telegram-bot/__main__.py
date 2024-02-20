import amazon_page_analyser as apa

import random
import time

from dotenv import load_dotenv  # load variables from .env file
import os

import telegram
import asyncio

import json


def get_random_product_info(deals_ids, already_sent_products_ids):
    if(len(deals_ids) == 0):
        return None

    selected_deal_id = random.choice(deals_ids)  # select a random product to get the info
    selected_product_info = apa.get_product_info(selected_deal_id)  # it may be None in case of some errors while scraping the page

    while True:  # get new product until the selected one is valid
        if (selected_product_info is not None) and (
                selected_product_info[
                    "product_id"] not in already_sent_products_ids):  # product valid and not already sent
            break

        deals_ids.remove(selected_deal_id)  # remove invalid product to not encounter it in the next iteration

        if(len(deals_ids) == 0):  # avoid infinte loop if there are no more products
            return None

        selected_deal_id = random.choice(deals_ids)
        selected_product_info = apa.get_product_info(random.choice(deals_ids))

    already_sent_products_ids.append(selected_product_info["product_id"])
    # it is necessary to save used products ids and not only remove them from the list because the list is recreated every few hours

    while(len(already_sent_products_ids) >= 100):
        already_sent_products_ids.pop(0)  # remove the oldest products sent if enough time has passed

    # return the selected product and the updated list of ids of products already sent
    # the list deals_ids is not returned because: (1) it is frequently recreated, (2) an invalid id may become valid in the future if the error was temporary
    return selected_product_info, already_sent_products_ids


def send_deal(bot, product_info, chat_id):
    if(product_info == None):
        return

    emoticon = ['\U0000203C', '\U00002757', '\U0001F525', '\U000026A1', '\U00002728']  # elements of message
    starting_text = ['A soli ', 'Solamente ', 'Soltanto ', 'Appena ', 'Incredibilmente solo ', 'Incredibilmente soltanto ']
    comparison_text = ['invece di ', 'al posto di ', 'piuttosto che ']

    caption = "<b>" + product_info["title"] + "</b>" + "\n\n"
    caption += "\U0001F449 " + apa.url_from_id(product_info["product_id"]) + "\n\n"  # add affiliate code here if any
    caption += random.choice(emoticon) + product_info["discount_rate"] + "\n"
    caption += "\U0001F4B6 " + random.choice(starting_text) + product_info["new_price"] + ", " + random.choice(comparison_text) + \
               "<del>" + product_info["old_price"] + "</del> " + random.choice(emoticon)

    asyncio.run(bot.send_photo(chat_id, product_info["image_link"], caption, parse_mode="HTML"))

    print("\nMessage sent:\n" + caption + "\n")

# This whole script is executed every time a new message needs to be sent.
# For this reason it is necessary to save data in a json file to avoid scraping every time the deals,
# and to avoid sending the same deals back to back.
# An alternative would be to have a while loop with a delay, but it would not be optimised for cron, which can be used schedule deals messages.
if __name__ == '__main__':

    load_dotenv(".env")

    new_collection_time = None
    already_sent_product_ids = []

    # if json file with already scraped deals exists
    try:

        with open("deals_ids.json", "r") as file:

            deals_dict = json.load(file)
            deals_ids = deals_dict["deals_ids"]
            already_sent_product_ids = deals_dict["already_sent_product_ids"]
            if time.time() - float(deals_dict["collection_time"]) > 2*3600:     # update deals every 2 hours
                deals_ids = apa.get_all_deals_ids()
                new_collection_time = time.time()

    # cannot open the file, load from web
    except OSError as e:
        deals_ids = apa.get_all_deals_ids()
        new_collection_time = time.time()

    # connect to the telegram bot
    bot = telegram.Bot(token=os.environ.get("AMAZON_DEALS_TG_BOT_TOKEN"))

    selected_product_info, already_sent_product_ids = get_random_product_info(deals_ids, already_sent_product_ids)
    send_deal(bot, selected_product_info, chat_id=os.environ.get("AMAZON_DEALS_TG_CHANNEL_ID"))

    # save deals collection time, the ids of new deals and the ids of the already sent products in a json file
    new_deals_dict = {"collection_time": new_collection_time if new_collection_time else deals_dict["collection_time"],
                      "deals_ids": deals_ids,
                      "already_sent_product_ids": already_sent_product_ids}
    with open("deals_ids.json", "w") as file:
        json.dump(new_deals_dict, file)
