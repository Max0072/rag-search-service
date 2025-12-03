"""
Search Engine with Filter Pipeline

Architecture:
1. Metadata Filters → narrow down scope (cheap)
2. Semantic Filters → find relevant content (expensive)
3. Post-processing → score filtering, field selection, sorting
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models import SearchFilter, ChunkResult
from app.database.vector_db import get_vector_db
from app.database.main_db import get_main_db
from app.database.embeddings import get_embedding_service


class SearchEngine:
    """
    Unified search engine with filter pipeline

    Process:
    Step 1: Metadata filters (fast) - reduce search space
    Step 2: Semantic search (slow) - find relevant chunks/summaries
    Step 3: Post-process - filter by score, select fields, sort
    """

    def __init__(self):
        self.vector_db = get_vector_db()
        self.main_db = get_main_db()
        self.embedding_service = get_embedding_service()

    def search(self,
               filter: SearchFilter,
               top_k: int = 10,
               min_score: float = 0.0,
               fields: List[str] = None,
               sort_by: str = None,
               sort_order: str = "desc") -> List[ChunkResult]:

        # Если fields не указан, вернуть все доступные поля
        if fields is None:
            fields = ["call_id", "date", "attendants", "meeting_type", "chunk_text", "chunk_index", "score"]

# ------ Step 1: Metadata Filtration (найти подходящие звонки) ------------
        calls = self.main_db.get_calls(
                    call_ids=filter.call_id,
                    date_from=filter.date_range.from_date if filter.date_range else None,
                    date_to=filter.date_range.to_date if filter.date_range else None,
                    attendants=filter.attendants,
                    meeting_type=filter.meeting_type
        )
        call_ids = [call.call_id for call in calls]

        # Если нет подходящих звонков - вернуть пустой результат
        if not call_ids:
            return []

# ------ Step 2: Semantic Search (поиск в векторной БД) ------------------------------------
        relevant_chunks = []
        relevant_summaries = []


        if filter.chunks and filter.summaries:
            raise ValueError("Impossible to find relevant chunks/summaries at the same time")


        # Поиск по chunks (если указан фильтр)
        if filter.chunks:
            relevant_chunks = self.search_by_chunks(filter.chunks, call_ids, top_k, min_score)
        # [{"call_id", "chunk", "score"}, ... ]
            call_ids = list(set([chunk["call_id"] for chunk in relevant_chunks]))


        # Поиск по summaries (если указан фильтр)
        elif filter.summaries:
            relevant_summaries = self.search_by_summary(filter.summaries, call_ids, top_k, min_score)
        # [{"call_id", "score"}, ... ]
            call_ids = list(set([summary["call_id"] for summary in relevant_summaries]))

# ------ Step 3: Post-processing и формирование результатов ---------------
        # Создать словарь для быстрого доступа к данным звонков
        calls_map = {call.call_id: call for call in calls}


        # Chunk separated list
        if filter.chunks and ("chunk_text" in fields or "chunk_index" in fields or "score" in fields):
            result_list = []
            for chunk in relevant_chunks:
                _dict = {}
                call_info = calls_map.get(chunk["call_id"])

                if "chunk_text" in fields:
                    _dict["chunk_text"] = chunk["chunk"]
                if "chunk_index" in fields:
                    _dict["chunk_index"] = chunk["chunk_id"]
                if "call_id" in fields:
                    _dict["call_id"] = chunk["call_id"]
                if "score" in fields:
                    _dict["score"] = chunk["score"]

                for field in fields:
                    if field in ["chunk_text", "chunk_index", "call_id", "score"]:
                        continue
                    if hasattr(call_info, field):
                        value = getattr(call_info, field)
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        _dict[field] = value
                    else:
                        raise ValueError(f"Field {field} not found in {call_info}")


                result_list.append(ChunkResult(**_dict))


        # Call separated list
        else:
            result_list = []
            for call_id in call_ids:
                call_info = calls_map.get(call_id)

                # Get score from relevant_summaries
                score = 0
                if relevant_summaries:
                    for s in relevant_summaries:
                        if s["call_id"] == call_id:
                            score = s["score"]
                            break

                _dict = {}
                if "score" in fields:
                    _dict["score"] = score

                for field in fields:
                    if field in ["chunk_text", "chunk_index", "score"]:
                        continue
                    if hasattr(call_info, field):
                        value = getattr(call_info, field)
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        _dict[field] = value
                    else:
                        raise ValueError(f"Field {field} not found in {call_info}")

                result_list.append(ChunkResult(**_dict))

# ------ Step 4: Sorting ---------------
        # Сортировка результатов
        if sort_by == "relevance":
            print(result_list)
            # Сортировка по score
            result_list.sort(key=lambda x: x.score, reverse=(sort_order == "desc"))
        elif sort_by == "date":
            # Сортировка по дате
            result_list.sort(key=lambda x: x.date if hasattr(x, 'date') and x.date else "", reverse=(sort_order == "desc"))
        elif sort_by == "chunk_index":
            # Сортировка по chunk_index
            result_list.sort(key=lambda x: x.chunk_index if hasattr(x, 'chunk_index') and x.chunk_index else 0, reverse=(sort_order == "desc"))

        return result_list



# ------ Semantic search by chunks ----------------------------------------------
    def search_by_chunks(self, query, call_ids, top_k, min_score):
        query_vector = self.embedding_service.generate_embedding(query)
        results = self.vector_db.query(
            query_vector=query_vector,
            call_ids=call_ids,
            top_k=top_k,
            index_type="chunks"
        )
        retrieved_chunks = results.get('matches', [])
        relevant_chunks = []
        for chunk in retrieved_chunks:
            if chunk.score >= min_score:
                relevant_chunks.append({"call_id": chunk.metadata.get("call_id"),
                                        "chunk_id": chunk.metadata.get("chunk_id"),
                                        "chunk": chunk.metadata.get("text", ""),
                                        "score": chunk.score})
        return relevant_chunks


# ------ Semantic search by summaries ----------------------------------------------
    def search_by_summary(self, query, call_ids, top_k, min_score):
        query_vector = self.embedding_service.generate_embedding(query)
        results = self.vector_db.query(
            query_vector=query_vector,
            call_ids=call_ids,
            top_k=top_k,
            index_type="summaries"
        )
        retrieved_summaries = results.get('matches', [])
        relevant_summaries = []
        for summary in retrieved_summaries:
            if summary.score >= min_score:
                relevant_summaries.append({"call_id": summary.metadata.get("call_id"),
                                         "score": summary.score})
        return relevant_summaries





# ------- Singleton instance ----------------------------------------------------------------------
_search_engine = None

def get_search_engine() -> SearchEngine:
    """Get singleton search engine instance"""
    global _search_engine
    if _search_engine is None:
        _search_engine = SearchEngine()
    return _search_engine


if __name__ == "__main__":
    pass
