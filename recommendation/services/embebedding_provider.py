from numpy import ndarray
from sentence_transformers import SentenceTransformer
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer

sentence_bert_model = SentenceTransformer('temp/models/sinhala-roberta-sentence-transformer')

try:
    with open('temp/models/xgboost/tfidf_vectorizer.pkl', 'rb') as f:
        tfidf_vectorizer: TfidfVectorizer = pickle.load(f)
    _tfidf_vectorizer_ready = True
except Exception as e:
    print(f"Could not load TF-IDF vectorizer: {e}")
    tfidf_vectorizer = TfidfVectorizer()
    _tfidf_vectorizer_ready = False


def get_sbert_embeddings(text_documents: list[str]):
    return sentence_bert_model.encode(text_documents)

def get_sbert_embedding(text_document: str) -> ndarray:
    return sentence_bert_model.encode(text_document)

def get_tfidf_embeddings(text_documents: list[str]):
    if not _tfidf_vectorizer_ready:
        raise RuntimeError(
            "TF-IDF vectorizer failed to load from temp/models/xgboost/tfidf_vectorizer.pkl. "
            "Run evaluations/train_xgboost.py to (re)generate it."
        )
    return tfidf_vectorizer.transform(text_documents)
