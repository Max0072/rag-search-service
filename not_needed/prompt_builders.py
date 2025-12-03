from abc import ABC, abstractmethod
from typing import List

class BasePromptBuilder(ABC):
    @abstractmethod
    def get_prompt(self, query: str, relevant_chunks: List) -> List[str]:
        pass


class BasicPromptBuilder(BasePromptBuilder):
    def __init__(self, base_prompt: str = ""):
        if base_prompt == "":
            self.base_prompt = \
"""You are an assistant that answers questions **strictly using the provided context**.
Follow these rules:

1. Use only the information from the context chunks.
2. If the answer is not found in the context, reply: 
   “The provided documents do not contain the answer.”
3. Do not use any outside knowledge.
4. Do not hallucinate or add information not present in the chunks.
5. If chunks contain conflicting information, highlight this clearly.
6. Give a clear, concise, and accurate answer.

# Query:
{query}

# Context:
{context}"""

    def get_prompt(self, query: str, relevant_chunks: List):
        context_chunks = '\n'.join(relevant_chunks)
        prompt = [f"{self.base_prompt}\n\n# Query:\n{query}\n\n# Context:\n{context_chunks}"]
        return prompt