"""Search module."""

import os
import warnings

import requests, time
from random import uniform
from bs4 import BeautifulSoup
from loguru import logger

warnings.filterwarnings("ignore", module="bs4")


def search(query: str, num: int) -> list[str]:
    """Do a request and colleting result."""
    user_agent = os.getenv("USER_AGENT")
    search_link = os.getenv("SEARCH_LINK")
    cookie = os.getenv("COOKIE")
    user_black_list = os.getenv("BLACK_LIST").split(", ")
    user_black_list = [u.strip() for u in user_black_list if u.strip()]

    black_list = [
        # Yandex black list
        "https://passport.yandex.ru/",
        "https://yandexwebcache.net/",
        "https://yandex.ru/support/",
        "https://cloud.yandex.ru/",
        "https://yandex.ru/",
        "https://www.ya.ru",
        "https://yandex.cloud/",
        "https://market.yandex.ru/",
        "https://alice.yandex.ru",
        "https://yabs.yandex.ru/"
    ]

    # black_list += user_black_list

    url = f"{search_link}{query}"
    urls = []

    # page = requests.get(
    #     url,
    #     headers={
    #         "user-agent": user_agent,
    #         "cookie": cookie,
    #     },
    #     timeout=20,
    # )

    try:
        page = requests.get(
            url,
            headers={
                "user-agent": user_agent,
                "cookie": cookie,
            },
            timeout=20,
        )
        page.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error("Timeout while requesting search page: {}", url)
        return []
    except requests.exceptions.RequestException as e:
        logger.error("Request failed for {}: {}", url, e)
        return []
    
    soup = BeautifulSoup(page.text, "html.parser")

    for link in soup.find_all("a"):
        url = str(link.get("href"))

        black = False
        if url.startswith("http"):
            for black_url in black_list:
                if black_url in url:
                    print(f"black = {black_url}, main = {url}")
                    print("\n")
                    black = True
                    break
            # urls.append(url)
            if not black:
                urls.append(url)
                logger.debug("URL: {}", url)
            else:
                print(".")
                # logger.error("URL: {}", url)
    # print(urls)
    return urls[:num]


def extract_text(url: str) -> str:
    """Extract text from url."""
    # page = requests.get(url, timeout=40)
    # time.sleep(uniform(2,4))
    # soup = BeautifulSoup(page.text, "html.parser")
    # return soup.get_text()
    try:
        page = requests.get(url, timeout=40)
        page.raise_for_status()
        time.sleep(uniform(2, 4))
        soup = BeautifulSoup(page.text, "html.parser")
        return soup.get_text()
    except requests.exceptions.Timeout:
        logger.error("Timeout while fetching {}", url)
        return ""
    except requests.exceptions.RequestException as e:
        logger.error("Failed to fetch {}: {}", url, e)
        return ""

