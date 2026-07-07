from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.decorators import api_view

from news_app.models import News
from recommendation.models import UserFeedback

@api_view(['POST'])
def get_user_feedback(request: Request):

    user = request.user

    print(request.data)
    category = request.data.get('category')
    feedback_type = request.data.get('feedback_type')
    news_id = request.data.get('news_id')

    news_record = News.objects.filter(news_id = news_id).first()
    feedback_record, _ = UserFeedback.objects.get_or_create(user=user, news_item=news_record)
    feedback_record.feedback_type = feedback_type
    feedback_record.save()

    return Response()
