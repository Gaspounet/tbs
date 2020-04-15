#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import time
import urllib.request
import urllib.error
from functools import wraps


def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    :param logger: logger to use. If None, print
    :type logger: logging.Logger instance
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


@retry(urllib.error.HTTPError, tries=5, delay=60, backoff=2)
def urlopen_with_retry(request):
    return urllib.request.urlopen(request)


def get_keyforge_card_infos():
    expansions = [
        {
            "name": "Call of the Archons",
            "id": 341,
            "number_of_cards": 370,
            "cards": [],
            "houses": []
        },
        {
            "name": "Age of Ascencion",
            "id": 435,
            "number_of_cards": 370,
            "cards": [],
            "houses": []
        },
        {
            "name": "Worlds Collide",
            "id": 452,
            "number_of_cards": 405,
            "cards": [],
            "houses": []
        }
    ]
    all_cards_list = []
    all_houses_list = []
    for expansion in expansions:
        page = 1
        while len(expansion["cards"]) < expansion["number_of_cards"]:
            headers = {'User-Agent': 'KFTBS_mod/1.0.0'}
            print("Searching through deck list of expansion {}, page {}".format(
                expansion["name"], page)
            )
            req = urllib.request.Request(
                "https://www.keyforgegame.com/api/decks/?page={}&expansion={}&links=cards".format(page, expansion["id"]),
                None,
                headers
            )
            content = urlopen_with_retry(req)
            deck_data = json.load(content)
            for card in deck_data["_linked"]["cards"]:
                if card["expansion"] == expansion["id"] \
                        and not card["is_maverick"]:
                    if card not in expansion["cards"]:
                        expansion["cards"].append(card)
                        if len(expansion["cards"]) == \
                                expansion["number_of_cards"]:
                            break
            for house in deck_data["_linked"]["houses"]:
                if house not in expansion["houses"]:
                    expansion["houses"].append(house)
            print("Missing {}".format(
                expansion["number_of_cards"] - len(expansion["cards"])
            ))
            page += 1
            time.sleep(5)
        expansion["cards"].sort(key=lambda x: x["card_number"])
        expansion["houses"].sort(key=lambda x: x["id"])
        all_cards_list.extend(expansion["cards"])
        for house in expansion["houses"]:
            if house not in all_houses_list:
                all_houses_list.append(house)
    kf_info_path = "keyforge_info.json"
    cards_info_path = "all_cards.json"
    houses_info_path = "all_houses.json"
    with open(kf_info_path, "w", encoding="utf-8") as f:
        json.dump(expansions, f, indent=4, ensure_ascii=False)

    with open(cards_info_path, "w", encoding="utf-8") as f:
        json.dump(all_cards_list, f, indent=4, ensure_ascii=False)

    with open(houses_info_path, "w", encoding="utf-8") as f:
        json.dump(all_houses_list, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    get_keyforge_card_infos()
