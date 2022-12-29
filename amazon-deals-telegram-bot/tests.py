import amazon_page_analyser as apa

import threading

import json


def get_deals():
    selenium_driver = apa.start_selenium()
    deals_ids = apa.get_deals_ids(selenium_driver)  # get deals only once
    selenium_driver.quit()  # close everything that was created. Better not to keep driver open for much time
    return deals_ids  # could be None or could contain the deals ids


def test_all_ids(deals_ids, logging=False):  # WARNING: Uses all bandwidth possible
    # array are needed because threads cannot return values
    valid_ids = []  # store all valid ids
    discounts = []  # store the discounts to do the average later

    threads = []
    for id in deals_ids:
        # create a thread with function test_single_id and give every thread the same arguments
        thread = threading.Thread(target=test_single_id, args=(id, valid_ids, discounts,))
        threads.append(thread)
        thread.start()

    # wait for every thread to finish because continuing
    for t in threads:
        t.join()

    print("Number of all ids " + str(len(deals_ids)))
    print("Number of valid ids " + str(len(valid_ids)))
    print("Average discount " + str(sum(discounts) / len(valid_ids)))

    if logging:
        # save the invalid ids in a file
        with open("tests_log.json", "w") as file:
            json.dump({"total_ids_count": len(deals_ids),
                       "valid_ids_count": len(valid_ids),
                       "average_discount": sum(discounts) / len(valid_ids),
                       "invalid_ids_list": [item for item in deals_ids if item not in valid_ids]},
                      file)


def test_single_id(id, valid_ids, discounts):
    product_info = apa.get_product_info(id)

    if product_info is not None:
        valid_ids.append(id)
        discounts.append(int(product_info["discount_rate"][1:-1]))  # remove - and % from discount rate


if __name__ == '__main__':
    deals_ids = get_deals()
    test_all_ids(deals_ids, logging=True)
