import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.request import Request

from news_app.dto.news import NewsItem
from news_app.models import News
from news_app.services.classifier import Classifier
from recommendation.services.recommendation import get_recommended_articles

logger = logging.getLogger(__name__)


@login_required(login_url='/users/login_user')
def home(request):
    
    # Currently logged user
    current_user = request.user

    # Todays news articles
    todays_news_items: list[News] = News.objects.filter(date__date=datetime.date.today()).all()
    
    recommended_articles = get_recommended_articles(todays_news_items, logger, current_user)

    print(recommended_articles)

    render_context = {
        "news_item_list": recommended_articles,
        "extra_news_list": todays_news_items
    }

    return render(request, 'news_app/home.html', render_context)

@api_view(['POST'])
def classify_article(request: Request):

    print(request.data)

    news_document = request.data.get('news_document')
    model_type = request.data.get('model_type')

    classifer = Classifier()
    if model_type == 'light':
        predicted_label = classifer.xgb_classify(news_document)

    else: # 'heavy'
        news_item = NewsItem()
        news_item.content = news_document
        predicted_items = classifer.bert_classify([news_item])

        predicted_label = predicted_items[0].category

    return Response({
        'category': predicted_label
    })
