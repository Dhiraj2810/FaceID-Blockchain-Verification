import numpy as np
from typing import Dict, Any, Tuple
from app.config import settings


def compare_embeddings(
    target_embedding: np.ndarray,
    candidate_embedding: np.ndarray,
    threshold: float = None
) -> Dict[str, Any]:
    """
    Computes cosine similarity between target embedding and candidate embedding.
    Returns:
        {
            "similarity": 0.87,
            "matched": True,
            "reason": "MATCH: Similarity score (0.8700) >= threshold (0.7000)"
        }
    """
    if threshold is None:
        threshold = settings.FACE_MATCH_THRESHOLD

    emb_a = np.array(target_embedding, dtype=np.float32).flatten()
    emb_b = np.array(candidate_embedding, dtype=np.float32).flatten()

    norm_a = np.linalg.norm(emb_a)
    norm_b = np.linalg.norm(emb_b)

    if norm_a == 0 or norm_b == 0:
        return {
            "similarity": 0.0,
            "matched": False,
            "reason": "NO MATCH: Zero-length embedding vector provided"
        }

    similarity = float(np.dot(emb_a, emb_b) / (norm_a * norm_b))
    similarity = max(-1.0, min(1.0, similarity))
    similarity_score = round(similarity, 4)

    matched = similarity_score >= threshold
    if matched:
        reason = f"MATCH: Similarity score ({similarity_score:.4f}) >= threshold ({threshold:.4f})"
    else:
        reason = f"NO MATCH: Similarity score ({similarity_score:.4f}) < threshold ({threshold:.4f})"

    return {
        "similarity": similarity_score,
        "matched": matched,
        "reason": reason
    }


def compare_faces(
    embedding_a: np.ndarray,
    embedding_b: np.ndarray,
    threshold: float = None
) -> Tuple[float, bool]:
    """
    Backward-compatible tuple interface (similarity_score, matched).
    """
    res = compare_embeddings(embedding_a, embedding_b, threshold=threshold)
    return res["similarity"], res["matched"]

