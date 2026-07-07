from datetime import datetime

from recommendation.services.embebedding_provider import get_sbert_embedding


class NewsItem:
    def __init__(self) -> None:
        self.news_id: str
        self.heading: str
        self.content: str
        self.timestamp: datetime
        self.link_to_source: str
        self.category: str
    
    def get_content_embedding(self):
        """Returns the embedding representation of the content"""
        return get_sbert_embedding(self.content).tolist()

    def get_posix_timstamp(self):
        return self.timestamp.timestamp()
