from transformers import pipeline
from sinling import SinhalaTokenizer
from sinling import SinhalaStemmer
import xgboost as xgb

from news_app.constants.class_label_mapper import ID_TO_LABEL
from news_app.dto.news import NewsItem
from news_app.models import News
from recommendation.services.embebedding_provider import get_tfidf_embeddings

class Classifier:

    def __init__(self) -> None:
        self.bert_classifier_local_location = 'temp/models/sinbert-1810-categories-finetuned'
        self.bert_classifier_pipe = pipeline("text-classification", self.bert_classifier_local_location)
        self.content_max_length = 500
        self.xgb_classifier = xgb.XGBClassifier()
        self.xgb_classifier.load_model('temp/models/xgboost/xgbclassifier.json')

    def bert_classify_and_save(self, news_list: list[NewsItem]) -> list[NewsItem]:
        for news in news_list:
            
            saved_object = News.objects.filter(news_id=news.news_id).first()
            if not saved_object:
                news.content = self.preprocess(news.content)
                prediction = self.bert_classifier_pipe(news.content[:self.content_max_length])
                news.category = prediction[0]['label']

                # Save to database
                news_store = News()
                news_store.news_id = news.news_id
                news_store.heading = news.heading
                news_store.category = news.category
                news_store.link_to_source = news.link_to_source
                news_store.date = news.timestamp

                news_store.save()

            else:
                news.category = saved_object.category

        return news_list
    
    def bert_classify(self, news_list: list[NewsItem]) -> list[NewsItem]:
        preprocessed_news_content_list = [self.preprocess(news_item.content[:self.content_max_length]) for news_item in news_list]
        predictions = self.bert_classifier_pipe(preprocessed_news_content_list)

        for i, prediction in enumerate(predictions):
            news_list[i].category = prediction['label']

        return news_list
    
    def xgb_classify(self, news_document: str) -> str:
        embeddings = get_tfidf_embeddings(text_documents=[news_document])

        prediction = self.xgb_classifier.predict(embeddings)
        predicted_id = prediction[0]

        return ID_TO_LABEL.get(predicted_id)
        

    def preprocess(self, news_content: str):
        sinhala_tokenizer = SinhalaTokenizer()
        stemmer = SinhalaStemmer()
        
        tokens = sinhala_tokenizer.tokenize(news_content)
        stemmed = [stemmer.stem(token)[0] for token in tokens]
        
        return ' '.join(stemmed)
    