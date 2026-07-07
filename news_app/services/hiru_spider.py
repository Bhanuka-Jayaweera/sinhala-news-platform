import datetime
import re
import time
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from django.utils.timezone import make_aware

from news_app.dto.news import NewsItem
from news_app.services.spider_common import get_last_known_date
from sinhala_news_platform_backend.settings import HIRU_NEWS_ID_PREFIX

ARTICLE_URL_RE = re.compile(r'^https://hirunews\.lk/(\d+)/')
DATE_PUBLISHED_RE = re.compile(r'"datePublished"\s*:\s*"([^"]+)"')
SRI_LANKA_TZ = ZoneInfo('Asia/Colombo')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
}


class HiruSpider:
    """Scrapes hirunews.lk. Its category-listing pages only return a
    handful of items over plain HTTP (the rest loads via JS), so instead
    this collects every article link referenced anywhere on the homepage
    (top stories, tickers, category blocks all link to the same article
    URL pattern) and fetches each one for its full content."""

    def _load_article_links(self) -> list[str]:
        response = requests.get('https://hirunews.lk/', headers=HEADERS)
        soup = BeautifulSoup(response.content, 'html.parser')

        links = []
        seen_ids = set()
        for a in soup.find_all('a', href=True):
            match = ARTICLE_URL_RE.match(a['href'])
            if match and match.group(1) not in seen_ids:
                seen_ids.add(match.group(1))
                links.append(a['href'])

        return links

    def _parse_article_page(self, url: str) -> NewsItem:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.content, 'html.parser')

        heading_element = soup.select_one('h1.head-title')
        content_element = soup.select_one('div.description-content')
        date_match = DATE_PUBLISHED_RE.search(response.text)

        naive_timestamp = datetime.datetime.strptime(date_match.group(1), '%Y-%m-%d %H:%M:%S')

        news_item = NewsItem()
        news_item.heading = heading_element.get_text(strip=True)
        news_item.content = content_element.get_text(strip=True)
        news_item.timestamp = make_aware(naive_timestamp, timezone=SRI_LANKA_TZ)
        news_item.link_to_source = url
        news_item.news_id = f"{HIRU_NEWS_ID_PREFIX}_{ARTICLE_URL_RE.match(url).group(1)}"

        return news_item

    def load_latest_news_items(self) -> list[NewsItem]:
        last_known_date = get_last_known_date(HIRU_NEWS_ID_PREFIX)

        loaded_news_items: list[NewsItem] = []

        for url in self._load_article_links():
            try:
                news_item = self._parse_article_page(url)
            except Exception as e:
                print(f"Hiru: failed to parse {url}: {e}")
                continue

            time.sleep(1)

            if news_item.timestamp > last_known_date:
                loaded_news_items.append(news_item)

        return loaded_news_items
