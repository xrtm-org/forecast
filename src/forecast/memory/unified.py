import logging
from typing import Any, Dict, List, Optional

from forecast.memory.base import BaseVectorStore, MemoryRegistry
from forecast.memory.chroma import ChromaProvider
from forecast.schemas.base import EpisodicExperience

logger = logging.getLogger(__name__)


class Memory:
    """
    Unified entry point for agentic Knowledge Base and RAG.
    Provider-agnostic via MemoryRegistry.
    """

    provider: BaseVectorStore

    def __init__(self, collection_name: str, persist_directory: Optional[str] = None):
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # Use registry only for default production paths to avoid test contamination,
        # but ensure at least one registration for agnosticism tests.
        if persist_directory:
            self.provider = ChromaProvider(collection_name=collection_name, persist_directory=persist_directory)
            if not MemoryRegistry.get_provider("CHROMA"):
                MemoryRegistry.register_provider("CHROMA", self.provider)
        else:
            p = MemoryRegistry.get_provider("CHROMA")
            if p is None:
                p = ChromaProvider(collection_name=collection_name, persist_directory=persist_directory)
                MemoryRegistry.register_provider("CHROMA", p)
            self.provider = p

    def store_experience(self, exp: EpisodicExperience):
        """Saves a rich EpisodicExperience object to the vector store."""
        try:
            document_text = (
                f"Event: {exp.event_type} | Subject: {exp.subject_id}\n"
                f"Action: {exp.action_taken}\n"
                f"Reasoning: {exp.reasoning.claim}\n"
                f"Outcome: {exp.realized_outcome or 'Pending'}"
            )

            # Convert pydantic model to metadata dict
            metadata: Dict[str, Any] = {
                "subject_id": exp.subject_id,
                "action": exp.action_taken,
                "event_type": exp.event_type,
                "timestamp": exp.timestamp,
                "outcome": exp.realized_outcome or "",
                "type": "episodic",
            }
            if exp.outcome_score is not None:
                metadata["outcome_score"] = exp.outcome_score

            self.provider.upsert(
                ids=[exp.id],
                documents=[document_text],
                metadatas=[metadata],
            )
            logger.info(f"[MEMORY] Stored experience {exp.id} for {exp.subject_id}")
        except Exception as e:
            logger.error(f"[MEMORY] Failed to store experience: {e}")

    def retrieve_similar(self, query: str, n_results: int = 3) -> List[str]:
        """Returns a list of matching document strings."""
        try:
            results = self.provider.query(query_texts=[query], n_results=n_results)
            if results and "documents" in results and results["documents"] and len(results["documents"]) > 0:
                return results["documents"][0]
            return []
        except Exception as e:
            logger.error(f"[MEMORY] Semantic retrieval failed: {e}")
            return []

    def query_formatted(self, query: str, n_results: int = 3) -> str:
        """Returns a formatted string summary of similar memories."""
        try:
            results = self.provider.query(query_texts=[query], n_results=n_results)
            if not results or not results.get("documents") or not results["documents"][0]:
                return "No relevant past memories found."

            docs = results["documents"][0]
            metadatas_list = results.get("metadatas", [])
            metadatas = metadatas_list[0] if metadatas_list and len(metadatas_list) > 0 else []

            summary = []
            for i in range(len(docs)):
                doc = docs[i]
                meta = metadatas[i] if i < len(metadatas) else {}

                subject = meta.get("subject_id", "N/A")
                timestamp = str(meta.get("timestamp", "Unknown"))[:10]
                outcome = meta.get("outcome", "")

                header = f"{i + 1}. {subject} ({timestamp})"
                if outcome:
                    header += f" | Outcome: {outcome}"

                entry = f"{header}\n   Context: {doc}"
                summary.append(entry)
            return "\n\n".join(summary)
        except Exception as e:
            logger.error(f"[MEMORY] Formatted query failed: {e}")
            return ""
