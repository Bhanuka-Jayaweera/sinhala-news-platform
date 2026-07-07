import datetime
from logging import Logger

import chromadb
import pandas as pd
from news_app.models import News
from recommendation.models import UserFeedback
import numpy as np
from sklearn.decomposition import NMF
from django.contrib.auth.models import User

from recommendation.services.vector_db_provider import get_chroma_db_collection
from sinhala_news_platform_backend.settings import MAXIMUM_NO_OF_SUGGESTED_ARTICLES

def get_recommended_articles(todays_news_items, logger: Logger, current_user: User):

    chroma_collection = get_chroma_db_collection()

    # Load previously liked news (from News)
    user_feedbacks = UserFeedback.objects.filter(user=current_user, feedback_type='positive').all()

    # News articles that the user has liked before
    liked_news_items: list[News] = [user_feedback.news_item for user_feedback in user_feedbacks]

    liked_embddings: list = []
    if liked_news_items:
        liked_articles_details: chromadb.GetResult = chroma_collection.get(
            ids=[liked_new_item.news_id for liked_new_item in liked_news_items],
            include=['embeddings']
        )
        # Some liked items may not have an embedding in Chroma yet (e.g. the
        # ingestion job hadn't written it when the user liked the article).
        liked_embddings = liked_articles_details.get('embeddings') or []

    if liked_embddings:

        # There are some pre liked items available, proceed with them
        print('Like history found. Recommendation processing...')

        resulted_article_details: chromadb.QueryResult = chroma_collection.query(
            query_embeddings=liked_embddings,
            n_results=5,
            where={'timestamp': {'$gte': datetime.datetime.combine(datetime.datetime.today(), datetime.time.min).timestamp()}},
            include=['distances']
        )
        ids = []
        distances = []
        for resulted_article_detail_ids in resulted_article_details.get('ids'):
            ids.extend(resulted_article_detail_ids)
        for resulted_article_detail_distances in resulted_article_details.get('distances'):
            distances.extend(resulted_article_detail_distances)

        article_details_df = pd.DataFrame({
            'id': ids,
            'distances': distances
        })
        # Chroma's default space is L2 distance: smaller distance = more similar.
        article_details_df = article_details_df.sort_values(by='distances', ascending=True).head(MAXIMUM_NO_OF_SUGGESTED_ARTICLES)
        
        resulted_articles = News.objects.filter(news_id__in=article_details_df['id'].values).all()
    
    else:
        # The user seems to be new user or they have never liked/disliked any article before
        # Suggest some articles based on matrix factorization
        logger.info('User has not liked any previous articles. Suggesting articles using matrix factorization.')

        all_users = User.objects.all()
        user_id_list = [user.id for user in all_users]
        news_id_list = [news_item.id for news_item in todays_news_items]

        current_user_id = current_user.id
        news_item_map: dict = dict()

        matrix = []
        for i, user_id in enumerate(user_id_list):

            if user_id == current_user.id:
                # Find the row index of matrix of current user
                current_user_id = i

            user_vector = []
            for j, news_id in enumerate(news_id_list):
                news_item_map[j] = news_id
                user_vector.append(int(UserFeedback.objects.filter(news_item_id=news_id, user_id=user_id).exists()))

            if not user_vector:
                user_vector.append(0)

            matrix.append(user_vector)

        # This sparse matrix would look like below where the rows represents a user and columns represents the news items
        # R = np.array([
        #     [0, 0, 0, 0],
        #     [1, 0, 0, 1],
        #     [1, 1, 0, 1],
        #     [1, 0, 0, 1],
        #     [0, 1, 1, 1],
        # ])
        R = np.array(matrix)

        # Perform matrix factorization
        model = NMF(n_components=2, init='random', random_state=0)
        U = model.fit_transform(R)
        V = model.components_

        def recommend_items(user_id, n):
            if np.all(R[user_id] == 0):
                # For new users, recommend based on overall popularity
                item_scores = np.sum(R, axis=0)
            else:
                # Predict interactions for all items
                item_scores = np.dot(U[user_id], V)
            
            # Get indices of top N items, excluding already interacted items
            interacted_items = np.where(R[user_id] > 0)[0]
            uninteracted_items = np.setdiff1d(np.arange(R.shape[1]), interacted_items)
            top_items = uninteracted_items[np.argsort(item_scores[uninteracted_items])[-n:][::-1]]
            
            return top_items

        
        recommended_items = recommend_items(current_user_id, n=MAXIMUM_NO_OF_SUGGESTED_ARTICLES)

        # Translate matrix index to actual news id
        recommended_items = [news_item_map.get(item) for item in recommended_items]
        print(f"Recommended items for user {current_user_id}: {recommended_items}")

        resulted_articles = News.objects.filter(pk__in=recommended_items).all()

        logger.info(resulted_articles)

    return resulted_articles
