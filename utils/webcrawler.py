"""Search and crawl module with history and document parsing."""

import os
import time
import warnings
import hashlib
import sqlite3
from random import uniform
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from loguru import logger

# Optional dependencies for document parsing
from PyPDF2 import PdfReader
from docx import Document

warnings.filterwarnings("ignore", module="bs4")

DB_PATH = "crawl_history.db"

# --------------------------------------------------------------------
# Database handler for crawl history
# --------------------------------------------------------------------
class CrawlHistory:
    """Manage crawled URLs and prevent re-processing."""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._create_table()

    def _get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _create_table(self):
        conn = self._get_connection()
        conn.execute("""
        CREATE TABLE IF NOT EXISTS crawled (
            url TEXT PRIMARY KEY,
            last_crawled REAL,
            content_hash TEXT,
            status_code INTEGER,
            error TEXT,
            content TEXT
        )
        """)
        conn.commit()
        conn.close()

    def _hash_content(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest() if text else None

    def get_cached_content(self, url: str) -> str | None:
        """Return stored text for already crawled URLs."""
        conn = self._get_connection()
        cur = conn.execute("SELECT content FROM crawled WHERE url = ?", (url,))
        row = cur.fetchone()
        conn.close()
        if row and row[0]:
            return row[0]
        return None

    def add_entry(self, url: str, text: str, status_code: int = 200, error: str | None = None):
        h = self._hash_content(text)
        conn = self._get_connection()
        conn.execute("""
        INSERT OR REPLACE INTO crawled (url, last_crawled, content_hash, status_code, error, content)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (url, time.time(), h, status_code, error, text))
        conn.commit()
        conn.close()


history = CrawlHistory()


# --------------------------------------------------------------------
# Search function
# --------------------------------------------------------------------
def search(query: str, num: int) -> list[str]:
    """Do a request and collect result URLs."""
    user_agent = os.getenv("USER_AGENT")
    search_link = os.getenv("SEARCH_LINK")
    cookie = os.getenv("COOKIE", "")
    user_black_list = os.getenv("BLACK_LIST", "").split(", ")
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
        "https://translate.yandex.ru/",
        "https://company.yandex"
    ]
    black_list += user_black_list

    url = f"{search_link}{query}"
    urls = []

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

    for link in soup.find_all("a", href=True):
        href = link["href"]
        if not href.startswith("http"):
            continue

        black = False
        for black_url in black_list:
            if black_url in href:
                black = True
                break

        if not black:
            if href not in urls:
                urls.append(href)
                logger.debug("URL: {}", href)

    return urls[:num]


# --------------------------------------------------------------------
# Document extraction utilities
# --------------------------------------------------------------------
def extract_pdf_text(file_path: str) -> str:
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() or ""
    except Exception as e:
        logger.error("PDF extraction failed for {}: {}", file_path, e)
    return text


def extract_docx_text(file_path: str) -> str:
    text = ""
    try:
        doc = Document(file_path)
        text = "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        logger.error("DOCX extraction failed for {}: {}", file_path, e)
    return text


# --------------------------------------------------------------------
# Text extraction from HTML or documents
# --------------------------------------------------------------------
def extract_text(url: str) -> str:
    """Extract text from a webpage or downloadable document."""
    cached_text = history.get_cached_content(url)
    if cached_text:
        logger.info("Using cached content for already processed URL: {}", url)
        return cached_text

    user_agent = os.getenv("USER_AGENT")
    cookie = os.getenv("COOKIE")
    headers={
                "user-agent": user_agent,
                "cookie": cookie,
    }

    try:
        response = requests.get(url, headers=headers, timeout=40)
        response.raise_for_status()

        # Handle PDFs
        if url.lower().endswith(".pdf"):
            file_path = "temp.pdf"
            with open(file_path, "wb") as f:
                f.write(response.content)
            text = extract_pdf_text(file_path)
            history.add_entry(url, text, status_code=response.status_code)
            return text

        # Handle DOCX
        elif url.lower().endswith(".docx"):
            file_path = "temp.docx"
            with open(file_path, "wb") as f:
                f.write(response.content)
            text = extract_docx_text(file_path)
            history.add_entry(url, text, status_code=response.status_code)
            return text

        # Handle normal web pages
        time.sleep(uniform(2, 4))
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        history.add_entry(url, text, status_code=response.status_code)
        return text

    except requests.exceptions.Timeout:
        logger.error("Timeout while fetching {}", url)
        history.add_entry(url, "", error="timeout")
        return ""
    except requests.exceptions.RequestException as e:
        logger.error("Failed to fetch {}: {}", url, e)
        history.add_entry(url, "", error=str(e))
        return ""
