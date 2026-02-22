from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseVectorStore(ABC):

    @abstractmethod
    async def similarity_search(
        self,
        embedding: List[float],
        workspace_id: str,
        assistant_id: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        pass
