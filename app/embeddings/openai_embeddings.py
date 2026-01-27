"""
Embeddings generation using OpenAI
"""

from typing import List
from openai import OpenAI
from app.config import get_settings

settings = get_settings()


class EmbeddingService:
    """Service for generating embeddings"""

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.embedding_model
        self.dimension = settings.embedding_dimension

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
            encoding_format="float",
            dimensions=self.dimension  # Specify dimension to match Pinecone index
        )
        return response.data[0].embedding

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=texts,
            encoding_format="float",
            dimensions=self.dimension  # Specify dimension to match Pinecone index
        )
        return [item.embedding for item in response.data]


# Singleton instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get singleton embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service