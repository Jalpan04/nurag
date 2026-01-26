
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import settings

class ChromaClient:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = chromadb.PersistentClient(
                path=settings.CHROMA_DB_DIR,
                settings=ChromaSettings(allow_reset=True, anonymized_telemetry=False)
            )
        return cls._instance

def get_chroma_client():
    return ChromaClient.get_instance()

def get_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(name=settings.CHROMA_COLLECTION_NAME)
