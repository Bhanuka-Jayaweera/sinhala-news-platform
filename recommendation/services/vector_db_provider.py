import chromadb

from sinhala_news_platform_backend.settings import CHROMA_DB_COLLECTION_NAME


def get_chroma_db_collection() -> chromadb.Collection:
    chroma_client = chromadb.PersistentClient()
    return chroma_client.get_or_create_collection(name=CHROMA_DB_COLLECTION_NAME)
