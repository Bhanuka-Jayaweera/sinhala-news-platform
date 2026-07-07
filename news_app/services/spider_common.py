import datetime

from news_app.models import News

DEFAULT_CURSOR_DATE = datetime.datetime(1990, 1, 1, tzinfo=datetime.timezone.utc)


def get_last_known_date(id_prefix: str) -> datetime.datetime:
    """Returns the date of the most recently saved News item for the given
    source (identified by its news_id prefix), or a very old default date
    if no items from that source have been saved yet."""
    last_item = News.objects.filter(news_id__startswith=f'{id_prefix}_').order_by('-date').first()
    return last_item.date if last_item else DEFAULT_CURSOR_DATE
