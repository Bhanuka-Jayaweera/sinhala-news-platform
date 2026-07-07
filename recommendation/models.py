from django.db import models
from django.contrib.auth.models import User
import pandas as pd

from news_app.models import News

class UserFeedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    news_item = models.ForeignKey(News, on_delete=models.DO_NOTHING)
    feedback_type = models.CharField(max_length=50)

    @classmethod
    def to_pandas(cls, item_list):
        users = []
        news_items = []
        feedback_types = []
        categories = []

        for item in item_list:
            users.append(item.user)
            news_items.append(item.news_item)
            feedback_types.append(item.feedback_type)
            categories.append(item.news_item.category)
        
        return pd.DataFrame({
            'user': users,
            'news_item': news_items,
            'feedback_types': feedback_types,
            'category': categories
        })
    
    @classmethod
    def get_distinct_categories(cls, item_list):
        
        categories = set()

        for item in item_list:
            news_item: News = item.news_item
            categories.add(news_item.category)

        return categories
    
