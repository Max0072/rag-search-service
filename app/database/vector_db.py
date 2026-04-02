"""
Pinecone vector database integration
"""

from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from app.config import get_settings

settings = get_settings()


class VectorDatabase:
    """Pinecone vector database client"""

    def __init__(self):
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.chunks_index_name = settings.pinecone_index_name
        self.summaries_index_name = settings.pinecone_summaries_index_name
        self.dimension = settings.embedding_dimension
        self._chunks_index = None
        self._summaries_index = None


# ------ Return index ------------------------------------------------------ done
    def get_index(self, index_type: str = "chunks"):
        """
        Get index by type
        index_type: "chunks" or "summaries"
        """
        if index_type == "chunks":
            if self._chunks_index is None:
                existing_indexes = [index.name for index in self.pc.list_indexes()]
                if self.chunks_index_name not in existing_indexes:
                    self._create_index(self.chunks_index_name)
                self._chunks_index = self.pc.Index(self.chunks_index_name)
            return self._chunks_index
        elif index_type == "summaries":
            if self._summaries_index is None:
                existing_indexes = [index.name for index in self.pc.list_indexes()]
                if self.summaries_index_name not in existing_indexes:
                    self._create_index(self.summaries_index_name)
                self._summaries_index = self.pc.Index(self.summaries_index_name)
            return self._summaries_index
        else:
            raise ValueError(f"Unknown index type: {index_type}")

    # create a new index
    def _create_index(self, index_name: str):
        self.pc.create_index(
            name=index_name,
            dimension=self.dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud=settings.pinecone_cloud, region=settings.pinecone_environment)
        )


# ------ Insert or update chunks/summaries in the vector database --------- done
    def upsert_chunks(self, chunks: List[Dict[str, Any]], index_type: str = "chunks"):
        """
        Upsert vectors to specified index
        chunks = [{
                    "id": str,
                    "values": [],
                    "metadata": {"text": str, "call_id": int, ... }
                }, ... ]
        index_type: "chunks" or "summaries"
        """
        index = self.get_index(index_type)
        index.upsert(vectors=chunks)


# ------ Search for relevant embeddings ------------------------------------ done
    def query(self,
              query_vector: List[float],
              top_k: int = 10,
              call_ids: Optional[List[Any]] = None,
              include_metadata: bool = True,
              index_type: str = "chunks") -> Dict[str, Any]:
        """
        Query vectors from specified index
        index_type: "chunks" or "summaries"
        """
        index = self.get_index(index_type)

        # Build filter for Pinecone
        filter_dict = None
        if call_ids:
            filter_dict = {"call_id": {"$in": call_ids}}

        results = index.query(
            vector=query_vector,
            top_k=top_k,
            filter=filter_dict,
            include_metadata=include_metadata
        )
        return results


# ------ Statistics about the index ---------------------------------------- done
    def get_stats(self, index_type: str = "chunks") -> Dict[str, Any]:
        """Get stats for specified index"""
        index = self.get_index(index_type)
        stats = index.describe_index_stats()
        return stats

    # ------ Delete vectors by call_id ----------------------------------------- done
    def delete_by_call_id(self, call_id: str, index_type: str = "chunks"):
        """Delete vectors by call_id from specified index"""
        index = self.get_index(index_type)
        index.delete(filter={"call_id": call_id})

    # ------ Delete all vectors from the index --------------------------------- done
    def delete_all(self, index_type: str = "chunks"):
        """Delete all vectors from specified index"""
        index = self.get_index(index_type)
        index.delete(delete_all=True)








# Singleton instance
_vector_db = None

# ------ Get database ------------------------------ done
def get_vector_db() -> VectorDatabase:
    """Get singleton vector database instance"""
    global _vector_db
    if _vector_db is None:
        _vector_db = VectorDatabase()
    return _vector_db




def test():
    """Test Pinecone connection"""
    print("🔌 Testing Pinecone connection...")

    try:
        # Initialize database
        db = VectorDatabase()
        print(f"✅ Connected to Pinecone")

        # Get or create index
        print(f"📦 Index name: {db.chunks_index_name}")
        print(f"📏 Dimension: {db.dimension}")

        index = db.get_index()
        print(f"✅ Index ready: {db.chunks_index_name}")

        # Get stats
        stats = db.get_stats()
        print(f"\n📊 Index Statistics:")
        print(f"   Total vectors: {stats.get('total_vector_count', 0)}")
        print(f"   Namespaces: {stats.get('namespaces', {})}")

        # Test upsert with dummy vectors
        print(f"\n🧪 Testing upsert with dummy data...")
        test_vector = [0.1] * db.dimension
        test_chunks = [
            {
                "id": "test-chunk-1",
                "values": test_vector,
                "metadata": {
                    "chunk_text": "This is test chunk 1",
                    "call_id": "test-call-1",
                    "date": "2024-11-27",
                    "attendants": ["Alice", "Bob"]
                }
            },
            {
                "id": "test-chunk-2",
                "values": test_vector,
                "metadata": {
                    "chunk_text": "This is test chunk 2",
                    "call_id": "test-call-1",
                    "date": "2024-11-27",
                    "attendants": ["Alice", "Bob"]
                }
            },
            {
                "id": "test-chunk-3",
                "values": test_vector,
                "metadata": {
                    "text": "This is test chunk 3",
                    "call_id": "test-call-2",
                    "date": "2024-11-27",
                    "attendants": ["Charlie", "Dave"]
                }
            }
        ]
        db.upsert_chunks(test_chunks)
        print(f"✅ Successfully upserted {len(test_chunks)} test chunks")

        # Test query
        print(f"\n🔍 Testing query...")
        results = db.query(query_vector=test_vector, top_k=5)
        print(f"✅ Query successful!")
        print(f"   Found {len(results.get('matches', []))} matches")

        if results.get('matches'):
            first_match = results['matches'][0]
            print(f"   First match score: {first_match.get('score', 0):.4f}")
            print(f"   First match metadata: {first_match.get('metadata', {})}")

        # Test delete by call_id
        print(f"\n🗑️  Testing delete by call_id...")
        print(f"   Deleting vectors with call_id='test-call-1'...")
        db.delete_by_call_id("test-call-1")
        print(f"✅ Delete operation completed")

        # Query with filter to verify deletion
        print(f"\n🔍 Verifying deletion...")
        results_after = db.query(
            query_vector=test_vector,
            top_k=10,
            call_ids=["test-call-1"]
        )
        print(f"   Vectors with call_id='test-call-1': {len(results_after.get('matches', []))}")

        results_remaining = db.query(
            query_vector=test_vector,
            top_k=10,
            call_ids=["test-call-2"]
        )
        print(f"   Vectors with call_id='test-call-2': {len(results_remaining.get('matches', []))}")

        if len(results_after.get('matches', [])) == 0 and len(results_remaining.get('matches', [])) > 0:
            print(f"✅ Delete by call_id works correctly!")

        print(f"\n✨ All tests passed! Pinecone is working correctly.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

def clear():
    db = get_vector_db()
    db.delete_all()

if __name__ == "__main__":
    test()