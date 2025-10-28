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
        "https://yabs.yandex.ru/",
        "https://translate.yandex.ru/"
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

    # try:
    #     page = requests.get(
    #         url,
    #         headers={
    #             "user-agent": user_agent,
    #             # "cookie": cookie,
    #         },
    #         timeout=20,
    #     )
    #     page.raise_for_status()
    # except requests.exceptions.Timeout:
    #     logger.error("Timeout while requesting search page: {}", url)
    #     return []
    # except requests.exceptions.RequestException as e:
    #     logger.error("Request failed for {}: {}", url, e)
    #     return []
    headers={
                "user-agent": user_agent,
                "cookie": cookie,
    }
    try:
        page = requests.get(url, headers=headers, timeout=20)
        page.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if page.status_code == 403 and "wikipedia.org" in url:
            logger.warning("403 Forbidden — switching to Wikipedia API for %s", url)
            api_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "titles": url.split("/")[-1],
                "prop": "extracts",
                "explaintext": True
            }
            page = requests.get(api_url, params=params, headers=headers, timeout=20)
        else:
            raise

    
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
    # try:
    #     page = requests.get(url, timeout=40)
    #     page.raise_for_status()
    #     time.sleep(uniform(2, 4))
    #     soup = BeautifulSoup(page.text, "html.parser")
    #     return soup.get_text()
    # except requests.exceptions.Timeout:
    #     logger.error("Timeout while fetching {}", url)
    #     return ""
    # except requests.exceptions.RequestException as e:
    #     logger.error("Failed to fetch {}: {}", url, e)
    #     return ""
    user_agent = os.getenv("USER_AGENT")
    cookie = os.getenv("COOKIE")
    headers={
                "user-agent": user_agent,
                "cookie": cookie,
    }
    try:
        # Primary attempt
        page = requests.get(url, headers=headers, timeout=40)
        page.raise_for_status()
        time.sleep(uniform(1.5, 3.5))

        soup = BeautifulSoup(page.text, "html.parser")
        return soup.get_text()

    # except requests.exceptions.HTTPError as e:
    #     # Wikipedia-specific 403 fallback
    #     if "wikipedia.org" in url and "403" in str(e):
    #         logger.warning(f"403 Forbidden detected — using Wikipedia API for {url}")
    #         try:
    #             title = url.split("/")[-1]
    #             api_url = "https://en.wikipedia.org/w/api.php"
    #             params = {
    #                 "action": "query",
    #                 "format": "json",
    #                 "titles": title,
    #                 "prop": "extracts",
    #                 "explaintext": True
    #             }
    #             api_resp = requests.get(api_url, headers=headers, params=params, timeout=20)
    #             api_resp.raise_for_status()
    #             data = api_resp.json()
    #             page_data = next(iter(data["query"]["pages"].values()))
    #             return page_data.get("extract", "")
    #         except Exception as api_err:
    #             logger.error(f"Wikipedia API fallback failed for {url}: {api_err}")
    #             return ""
    #     else:
    #         logger.error(f"HTTPError for {url}: {e}")
    #         return ""

    except requests.exceptions.Timeout:
        logger.error(f"Timeout while fetching {url}")
        return ""

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return ""

