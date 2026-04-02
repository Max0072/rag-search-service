"""
Data Manager - synchronization between Vector DB and Metadata DB

This class provides:
- Adding calls with automatic chunking and indexing
- Deletion with cleanup from both databases
- Updating with chunk regeneration
- Data consistency between PostgreSQL and Pinecone
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import re

from app.database.main_db import get_main_db
from app.database.vector_db import get_vector_db
from app.embeddings.openai_embeddings import get_embedding_service
from app.config import get_settings

settings = get_settings()


class DataManager:
    """
    Unified data manager for conference calls

    Manages synchronization between:
    - Metadata DB (PostgreSQL) - full transcripts and metadata
    - Vector DB (Pinecone) - chunks with embeddings for search
    """

    def __init__(self):
        self.main_db = get_main_db()
        self.vector_db = get_vector_db()
        self.embedding_service = get_embedding_service()

        # Chunking configuration
        self.chunk_size = 512  # tokens/characters per chunk
        self.chunk_overlap = 50  # overlap between chunks


    def add_call(self, call_id: str, full_transcript: str, summary: str,
                date: datetime, attendants: List[str], topic: Optional[str] = None,
                meeting_type: Optional[str] = None, duration_minutes: Optional[int] = None,
                meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:

        try:

            # Step 1: Split transcript into chunks
            print(f"📝 Chunking transcript for call {call_id}...")
            chunks = self._chunk_transcript(full_transcript)
            chunks_count = len(chunks)
            print(f"   Created {chunks_count} chunks")

            # Step 2: Generate embeddings for all chunks
            print(f"🔢 Generating embeddings for {chunks_count} chunks...")
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedding_service.generate_embeddings_batch(chunk_texts)
            print(f"   Generated {len(embeddings)} embeddings")

            # Step 2.5: Generate embedding for summary
            print(f"📝 Generating embedding for summary...")
            summary_embedding = self.embedding_service.generate_embedding(summary)
            print(f"   Generated summary embedding")

            # Step 3: Store in PostgreSQL (metadata DB)
            print(f"💾 Storing call metadata in PostgreSQL...")
            call = self.main_db.create_call(
                call_id=call_id,
                full_transcript=full_transcript,
                summary=summary,
                date=date,
                attendants=attendants,
                topic=topic,
                meeting_type=meeting_type,
                duration_minutes=duration_minutes,
                meta=meta,
                chunks_count=chunks_count
            )
            print(f"   ✅ Stored in PostgreSQL")

            # Step 4: Prepare chunks for Pinecone
            print(f"📦 Preparing chunks for Pinecone...")
            pinecone_chunks = []
            for i, (chunk_data, embedding) in enumerate(zip(chunks, embeddings)):
                _id = f"{call_id}__chunk_{i}"

                pinecone_chunk = {
                    "id": _id,
                    "values": embedding,
                    "metadata": {
                        "call_id": call_id,
                        "chunk_id": i,
                        "text": chunk_data["text"],
                    }
                }
                pinecone_chunks.append(pinecone_chunk)

            # Step 5: Upload chunks to Pinecone
            print(f"🚀 Uploading {len(pinecone_chunks)} chunks to Pinecone...")
            self.vector_db.upsert_chunks(pinecone_chunks, index_type="chunks")
            print(f"   ✅ Uploaded chunks to Pinecone")

            # Step 6: Upload summary to Pinecone summaries index
            print(f"🚀 Uploading summary to Pinecone...")
            summary_vector = {
                "id": f"{call_id}__summary",
                "values": summary_embedding,
                "metadata": {
                    "call_id": call_id,
                }
            }
            self.vector_db.upsert_chunks([summary_vector], index_type="summaries")
            print(f"   ✅ Uploaded summary to Pinecone")

            print(f"✨ Successfully added call {call_id}")

            return {
                "call_id": call_id,
                "chunks_count": chunks_count,
                "status": "success",
                "message": f"Call added with {chunks_count} chunks"
            }

        except Exception as e:
            # Rollback: try to clean up what was created
            print(f"❌ Error adding call: {str(e)}")
            print(f"🔄 Attempting rollback...")

            try:
                # Delete from PostgreSQL if created
                self.main_db.delete_call(call_id)
                # Delete chunks from Pinecone
                self._delete_call_chunks(call_id)
                print(f"   ✅ Rollback successful")
            except:
                print(f"   ⚠️  Rollback partially failed - manual cleanup may be needed")

            raise Exception(f"Failed to add call: {str(e)}")


# ------ delete call from all databases ------------------------------------ done
    def delete_call(self, call_id: str) -> Dict[str, Any]:
        try:
            print(f"🗑️  Deleting call {call_id}...")
            # Delete from both indexes
            self.vector_db.delete_by_call_id(call_id, index_type="chunks")
            self.vector_db.delete_by_call_id(call_id, index_type="summaries")
            success = self.main_db.delete_call(call_id)

            if not success:
                return {"call_id": call_id, "status": "not_found", "message": f"Call {call_id} not found"}

            print(f"   ✅ Deleted from PostgreSQL")
            print(f"✨ Successfully deleted call {call_id}")
            return {"call_id": call_id, "status": "success", "message": "Call deleted successfully"}

        except Exception as e:
            raise Exception(f"Failed to delete call: {str(e)}")

# ------ update call ------------------------------------------------------- done
    def update_call(self, call_id: str, full_transcript: Optional[str] = None,
                    summary: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        try:
            print(f"✏️  Updating call {call_id}...")
            call = self.main_db.get_call(call_id)
            if not call:
                raise Exception(f"Call {call_id} not found")

            # transcript changed
            if full_transcript and full_transcript != call.full_transcript:
                print(f"   Transcript changed - regenerating chunks...")
                self.vector_db.delete_by_call_id(call_id, index_type="chunks")

                # Create new chunks
                chunks = self._chunk_transcript(full_transcript)
                chunk_texts = [chunk['text'] for chunk in chunks]
                embeddings = self.embedding_service.generate_embeddings_batch(chunk_texts)

                # Upload new chunks to Pinecone
                pinecone_chunks = []
                for i, (chunk_data, embedding) in enumerate(zip(chunks, embeddings)):
                    chunk_id = f"{call_id}__chunk_{i}"
                    pinecone_chunk = {
                        "id": chunk_id,
                        "values": embedding,
                        "metadata": {"call_id": call_id}
                    }
                    pinecone_chunks.append(pinecone_chunk)

                self.vector_db.upsert_chunks(pinecone_chunks, index_type="chunks")

                # Update chunks_count
                kwargs['chunks_count'] = len(chunks)
                print(f"   ✅ Regenerated {len(chunks)} chunks")

            # summary changed
            if summary and summary != call.summary:
                print(f"   Summary changed - regenerating embedding...")
                # Delete old summary
                self.vector_db.delete_by_call_id(call_id, index_type="summaries")

                # Generate new embedding
                summary_embedding = self.embedding_service.generate_embedding(summary)

                # Upload new summary
                summary_vector = {
                    "id": f"{call_id}__summary",
                    "values": summary_embedding,
                    "metadata": {"call_id": call_id}
                }
                self.vector_db.upsert_chunks([summary_vector], index_type="summaries")
                print(f"   ✅ Regenerated summary embedding")

            # Update in PostgreSQL
            if full_transcript:
                kwargs['full_transcript'] = full_transcript
            if summary:
                kwargs['summary'] = summary

            updated_call = self.main_db.update_call(call_id, **kwargs)

            if not updated_call:
                raise Exception(f"Failed to update call in database")

            print(f"✨ Successfully updated call {call_id}")

            return {
                "call_id": call_id,
                "status": "success",
                "message": "Call updated successfully"
            }

        except Exception as e:
            raise Exception(f"Failed to update call: {str(e)}")

# ------ get call ---------------------------------------------------------- done
    def get_call(self, call_id: str):
        return self.main_db.get_call(call_id)


# ------------------------------------------------------------------
    def sync_check(self) -> Dict[str, Any]:
        print("🔍 Checking database synchronization...")

        # Get all calls from PostgreSQL
        calls = self.main_db.get_calls(limit=1000)

        issues = []
        total_calls = len(calls)
        total_chunks_expected = sum(call.chunks_count for call in calls)

        for call in calls:
            # Check if chunks exist in Pinecone (simplified check)
            # In production, you'd query Pinecone to verify
            if call.chunks_count == 0:
                issues.append({"call_id": call.call_id, "issue": "No chunks indexed", "expected_chunks": 0})

        # Get stats from Pinecone
        vector_stats = self.vector_db.get_stats()
        total_chunks_actual = vector_stats.get("total_vector_count", 0)

        print(f"📊 Sync Status:")
        print(f"   PostgreSQL: {total_calls} calls, {total_chunks_expected} chunks expected")
        print(f"   Pinecone: {total_chunks_actual} chunks indexed")
        print(f"   Issues found: {len(issues)}")

        return {
            "status": "synced" if len(issues) == 0 else "issues_found",
            "total_calls": total_calls,
            "total_chunks_expected": total_chunks_expected,
            "total_chunks_actual": total_chunks_actual,
            "issues": issues
        }

    # ========== Private Helper Methods ==========

    def _chunk_transcript(self, transcript: str) -> List[Dict[str, Any]]:
        """
        Split transcript into chunks

        Simple chunking strategy:
        - Split by sentences
        - Group into chunks of ~chunk_size characters
        - Add overlap between chunks

        Args:
            transcript: Full transcript text

        Returns:
            List of chunk dictionaries with text and metadata
        """
        # Simple sentence splitter
        sentences = re.split(r'(?<=[.!?])\s+', transcript)

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            # If adding this sentence exceeds chunk size, save current chunk
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "speaker": "",  # TODO: extract from transcript if available
                    "timestamp": ""  # TODO: extract if available
                })

                # Start new chunk with overlap
                # Keep last few sentences for context
                overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                current_chunk = overlap_sentences
                current_length = sum(len(s) for s in overlap_sentences)

            current_chunk.append(sentence)
            current_length += sentence_length

        # Add last chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "speaker": "",
                "timestamp": ""
            })

        return chunks



# Singleton instance
_data_manager = None


def get_data_manager() -> DataManager:
    """Get singleton data manager instance"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager


if __name__ == "__main__":
    """Test data manager"""
    print("🧪 Testing Data Manager...\n")

    try:
        manager = get_data_manager()

        # Test: Add a call
        print("=" * 50)
        print("TEST 1: Add Call")
        print("=" * 50)

        result = manager.add_call(
            call_id="test-dm-001",
            full_transcript="""
            Alice: Hello everyone, thanks for joining today's meeting.
            Bob: Hi Alice, happy to be here. What's on the agenda?
            Alice: We need to discuss the Q4 roadmap and API integration issues.
            Charlie: I've been looking into the API problems. The main issue is timeout errors.
            Bob: How often are these happening?
            Charlie: About 15% of requests are timing out, especially during peak hours.
            Alice: That's concerning. What's causing it?
            Charlie: The database queries are taking too long. We need to add indexes.
            Bob: I can help with that. Should we also look at caching?
            Alice: Good idea. Let's prioritize both. Charlie, can you create tickets?
            Charlie: Will do. I'll have them ready by tomorrow.
            Alice: Perfect. Anything else we need to cover today?
            Bob: Just a quick update - the frontend redesign is on track for next week.
            Alice: Excellent. Thanks everyone, let's wrap up.
            """,
            summary="Q4 roadmap discussion and API timeout issues. Need to add database indexes and implement caching.",
            date=datetime.now(),
            attendants=["Alice", "Bob", "Charlie"],
            topic="Q4 Planning & API Issues",
            meeting_type="internal",
            duration_minutes=25,
            meta={
                "department": "engineering",
                "priority": "high"
            }
        )

        print(f"\n✅ Result: {result}\n")

        # Test: Sync check
        print("=" * 50)
        print("TEST 2: Sync Check")
        print("=" * 50)

        sync_status = manager.sync_check()
        print(f"\n✅ Sync Status: {sync_status}\n")

        # Test: Get call
        print("=" * 50)
        print("TEST 3: Get Call")
        print("=" * 50)

        call = manager.get_call("test-dm-001")
        if call:
            print(f"✅ Retrieved call: {call.call_id}")
            print(f"   Topic: {call.topic}")
            print(f"   Chunks: {call.chunks_count}")
            print(f"   Attendants: {call.attendants}")

        # Test: Delete call
        print("\n" + "=" * 50)
        print("TEST 4: Delete Call")
        print("=" * 50)

        delete_result = manager.delete_call("test-dm-001")
        print(f"\n✅ Delete Result: {delete_result}\n")

        print("=" * 50)
        print("✨ All tests passed!")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
