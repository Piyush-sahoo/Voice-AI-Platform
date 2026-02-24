import math
from typing import List, Dict, Any

from shared.database.connection import get_database
from .vector_store import BaseVectorStore


def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class MongoVectorStore(BaseVectorStore):

    async def similarity_search(
        self,
        embedding: List[float],
        workspace_id: str,
        assistant_id: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:

        db = get_database()

        cursor = db.knowledge_chunks.find({
            "workspace_id": workspace_id,
            "assistant_ids": assistant_id
        })

        scored = []

        async for doc in cursor:
            chunk_embedding = doc.get("embedding")
            if not chunk_embedding:
                continue

            score = cosine_similarity(embedding, chunk_embedding)
            doc["score"] = score
            scored.append(doc)

        scored.sort(key=lambda x: x["score"], reverse=True)

        return scored[:top_k]
