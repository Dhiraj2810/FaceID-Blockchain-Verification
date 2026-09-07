import numpy as np
from typing import Dict, Any, Union


def generate_embedding(face_data: Union[Dict[str, Any], np.ndarray]) -> np.ndarray:
    """
    Generates a 512-dimensional L2-normalized ArcFace embedding vector for a detected face.
    MUST come from the genuine InsightFace recognition model.
    Raises ValueError if a valid ArcFace embedding cannot be extracted.
    """
    raw_face = None

    if isinstance(face_data, dict):
        raw_face = face_data.get("raw_face")

    if raw_face is None:
        raise ValueError("Cannot generate embedding: Missing raw InsightFace object. Dummy/fallback embeddings are strictly disabled.")

    if hasattr(raw_face, "normed_embedding") and raw_face.normed_embedding is not None:
        embedding = np.array(raw_face.normed_embedding, dtype=np.float32)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            return embedding / norm
        return embedding
    elif hasattr(raw_face, "embedding") and raw_face.embedding is not None:
        embedding = np.array(raw_face.embedding, dtype=np.float32)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            return embedding / norm
        return embedding

    raise ValueError("InsightFace model failed to produce a valid ArcFace embedding vector.")
