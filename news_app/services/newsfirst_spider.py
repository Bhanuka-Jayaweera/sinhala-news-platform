import datetime
import hashlib
import re
import time
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from django.utils.timezone import make_aware

from news_app.dto.news import NewsItem
from news_app.services.spider_common import get_last_known_date
from sinhala_news_platform_backend.settings import NEWS1ST_NEWS_ID_PREFIX

BASE_URL = 'https://sinhala.newsfirst.lk'
ARTICLE_PATH_RE = re.compile(r'^/\d{4}/\d{2}/\d{2}/')
SRI_LANKA_TZ = ZoneInfo('Asia/Colombo')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
}


class NewsFirstSpider:
    """Scrapes sinhala.newsfirst.lk's /latest-news page (an Angular app,
    but server-rendered so plain HTTP sees full content). Pagination on
    that page is client-side only, so this only reads the first page --
    acceptable since the scheduler polls every 5 minutes."""

    def _load_article_links(self) -> list[str]:
        response = requests.get(f'{BASE_URL}/latest-news', headers=HEADERS)
        soup = BeautifulSoup(response.content, 'html.parser')

        links = []
        seen_paths = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if ARTICLE_PATH_RE.match(href) and href not in seen_paths:
                seen_paths.add(href)
                links.append(BASE_URL + href)

        return links

    def _parse_article_page(self, url: str) -> NewsItem:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.content, 'html.parser')

        heading_element = soup.select_one('h1.top_stories_header_news')
        content_element = soup.select_one('div.new_details')
        date_element = soup.select_one('div.author_main span')

        # e.g. "07-07-2026 | 7:33 AM"
        naive_timestamp = datetime.datetime.strptime(
            date_element.get_text(strip=True), '%d-%m-%Y | %I:%M %p'
        )

        news_item = NewsItem()
        news_item.heading = heading_element.get_text(strip=True)
        news_item.content = content_element.get_text(strip=True)
        news_item.timestamp = make_aware(naive_timestamp, timezone=SRI_LANKA_TZ)
        news_item.link_to_source = url
        # Article slugs are long, percent-encoded Sinhala text that can
        # exceed News.news_id's max_length, so hash them into a short id.
        news_item.news_id = f"{NEWS1ST_NEWS_ID_PREFIX}_{hashlib.md5(url.encode()).hexdigest()[:16]}"

        return news_item

    def load_latest_news_items(self) -> list[NewsItem]:
        last_known_date = get_last_known_date(NEWS1ST_NEWS_ID_PREFIX)

        loaded_news_items: list[NewsItem] = []

        for url in self._load_article_links():
            try:
                news_item = self._parse_article_page(url)
            except Exception as e:
                print(f"News1st: failed to parse {url}: {e}")
                continue

            time.sleep(1)

            if news_item.timestamp > last_known_date:
                loaded_news_items.append(news_item)

        return loaded_news_items
