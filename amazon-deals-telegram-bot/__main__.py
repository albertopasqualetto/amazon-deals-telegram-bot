import amazon_page_analyser as apa

import random
import time

from dotenv import load_dotenv  # load variables from .env file
import os

import telegram
import asyncio

import json

from urllib.parse import urlparse, parse_qs, urlencode

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger


CRON_EXPRESSION = os.environ.get("AMAZON_DEALS_TG_CRON_SCHEDULE") if os.environ.get("AMAZON_DEALS_TG_CRON_SCHEDULE") else "*/20 8-23 * * *"

OUTPUT_DEALS_FILE = "deals_ids.json" if not os.environ.get("IS_CONTAINERIZED") else "/data/deals_ids.json"  # file to save scraped deals ids


def get_random_product_info(deals_ids, already_sent_products_ids):
    if(len(deals_ids) == 0):
        return None

    selected_deal_id = random.choice(deals_ids)  # select a random product to get the info
    selected_product_info = apa.get_product_info(selected_deal_id)  # it may be None in case of some errors while scraping the page

    while True:  # get new product until the selected one is valid
        if (selected_product_info is not None) and (
                selected_product_info["product_id"] not in already_sent_products_ids):  # product valid and not already sent
            break

        deals_ids.remove(selected_deal_id)  # remove invalid product to not encounter it in the next iteration

        if(len(deals_ids) == 0):  # avoid infinte loop if there are no more products
            return None

        selected_deal_id = random.choice(deals_ids)
        selected_product_info = apa.get_product_info(random.choice(deals_ids))

    already_sent_products_ids.append(selected_product_info["product_id"])
    # it is necessary to save used products ids and not only remove them from the list because the list is recreated every few hours

    while(len(already_sent_products_ids) >= 50):
        already_sent_products_ids.pop(0)  # remove the oldest products sent if enough time has passed

    # return the selected product and the updated list of ids of products already sent
    # the list deals_ids is not returned because: (1) it is frequently recreated, (2) an invalid id may become valid in the future if the error was temporary
    return selected_product_info, already_sent_products_ids


'''
    Add affiliate id ('tag') parameter in url.

    If a previous one was present it is removed.
    If an empty string is passed (default), affiliate id is not added.
'''
def add_affiliate_id(url, affiliate_id=''):
    url_parts = urlparse(url)   # parse url parts
    query = parse_qs(url_parts.query, keep_blank_values=True)   # get parameters from url
    query.update({'tag': affiliate_id}) # add affiliate id
    if affiliate_id == '':  # if no affiliate id provided, do not add it
        query.pop('tag')
    return url_parts._replace(query=urlencode(query, doseq=True)).geturl()  # rebuild url


def send_deal(bot, product_info, chat_id):
    if(product_info == None):
        return

    emoticon = ['\U0000203C', '\U00002757', '\U0001F525', '\U000026A1', '\U00002728']  # elements of message
    starting_text = ['A soli ', 'Solamente ', 'Soltanto ', 'Appena ', 'Incredibilmente solo ', 'Incredibilmente soltanto ']
    comparison_text = ['invece di ', 'al posto di ', 'piuttosto che ']

    caption = "<b>" + product_info["title"] + "</b>" + "\n\n"
    caption += "\U0001F449 " + add_affiliate_id(apa.url_from_id(product_info["product_id"]), os.environ.get("AMAZON_DEALS_TG_AFFILIATE_ID")) + "\n\n"
    caption += random.choice(emoticon) + product_info["discount_rate"] + "\n"
    caption += "\U0001F4B6 " + random.choice(starting_text) + product_info["new_price"] + ", " + random.choice(comparison_text) + \
               "<del>" + product_info["old_price"] + "</del> " + random.choice(emoticon)

    asyncio.run(bot.send_photo(chat_id, product_info["image_link"], caption, parse_mode="HTML"))

    print("\nMessage sent:\n" + caption + "\n")


def retrieve_deals():
    # if json file with already scraped deals exists
    try:
        with open(OUTPUT_DEALS_FILE, "r") as file:
            deals_dict = json.load(file)
            download_new_deals = False
            if time.time() - float(deals_dict["collection_time"]) > 2*3600:     # update deals every 2 hours
                download_new_deals = True

    # cannot open the file, load from web
    except OSError as e:
        download_new_deals = True

    if download_new_deals:
        deals_dict = {"collection_time": time.time(),
                        "deals_ids": apa.get_all_deals_ids(),
                        "already_sent_product_ids": []}

    return deals_dict


# This whole code is executed every time a new message needs to be sent.
# For this reason it is necessary to save data in a json file to avoid scraping every time the deals,
# and to avoid sending the same deals back to back.
# An alternative would be to have a while loop with a delay, but it would not be optimized for cron, which can be used to schedule deals messages.
def run():
    print("Running...")
    deals_dict = retrieve_deals()
    collection_time = deals_dict["collection_time"]
    deals_ids = deals_dict["deals_ids"]
    already_sent_product_ids = deals_dict["already_sent_product_ids"]

    # connect to the telegram bot
    bot = telegram.Bot(token=os.environ.get("AMAZON_DEALS_TG_BOT_TOKEN"))

    selected_product_info, already_sent_product_ids = get_random_product_info(deals_ids, already_sent_product_ids)
    send_deal(bot, selected_product_info, chat_id=os.environ.get("AMAZON_DEALS_TG_CHANNEL_ID"))

    # save deals collection time, the ids of new deals and the ids of the already sent products in a json file
    new_deals_dict = {"collection_time": collection_time,
                      "deals_ids": deals_ids,
                      "already_sent_product_ids": already_sent_product_ids}
    with open(OUTPUT_DEALS_FILE, "w") as file:
        json.dump(new_deals_dict, file)
    print("Run completed.")


def delayed_run():
    print("Waiting a random time before running...")
    time.sleep(random.randint(0, 600))
    run()


if __name__ == '__main__':
    load_dotenv(".env")

    # First run
    run()

    if os.environ.get("IS_CONTAINERIZED"):
        print("Running in containerized environment. Scheduler will be added.")
        scheduler = BlockingScheduler()
        scheduler.add_job(delayed_run, CronTrigger.from_crontab(CRON_EXPRESSION))
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            pass
