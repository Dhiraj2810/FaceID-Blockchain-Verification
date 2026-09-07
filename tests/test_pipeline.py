import pytest
import tempfile
import cv2
import numpy as np
from pathlib import Path
from unittest.mock import patch
from app.pipeline.orchestrator import PipelineOrchestrator
from app.search.base import BaseReverseImageSearcher
from app.evidence.models import CandidateResult


class MockSearcher(BaseReverseImageSearcher):
    def __init__(self, candidate_image_path: str):
        self.candidate_image_path = candidate_image_path

    def search(self, image_path: str):
        return [
            CandidateResult(
                title="Mock Social Post",
                url="https://example.com/mock-post",
                thumbnail_url=self.candidate_image_path,
                source="Mock Provider"
            )
        ]


class DummyRawFace:
    def __init__(self):
        emb = np.random.randn(512).astype(np.float32)
        self.normed_embedding = emb / np.linalg.norm(emb)
        self.det_score = 0.95
        self.bbox = np.array([50, 50, 250, 250])


def test_pipeline_end_to_end():
    with tempfile.NamedTemporaryFile("wb", suffix=".jpg", delete=False) as f:
        img_path = f.name

    img = np.ones((400, 400, 3), dtype=np.uint8) * 220
    cv2.imwrite(img_path, img)

    raw_face = DummyRawFace()
    mock_detected_faces = ([{
        "bbox": [50, 50, 250, 250],
        "confidence": 0.95,
        "crop": img[50:250, 50:250],
        "raw_face": raw_face
    }], {"image_size": "400x400", "channels": 3, "detection_model": "SCRFD", "det_size": "1024x1024", "threshold": 0.3, "attempts": 1, "attempt_history": [], "faces_detected": 1})

    try:
        mock_searcher = MockSearcher(candidate_image_path=img_path)
        orchestrator = PipelineOrchestrator(searcher=mock_searcher)

        with patch("app.pipeline.orchestrator.detect_faces", return_value=mock_detected_faces), \
             patch("app.evidence.extractor.detect_faces", return_value=mock_detected_faces):

            res = orchestrator.run_pipeline(img_path, verbose=False, threshold=0.50)

            assert res.status == "success"
            assert res.face["detected"] is True
            assert res.search["candidates_found"] == 1
            assert res.match["found"] is True
            assert res.blockchain["registered"] is True
            assert res.verification["verified"] is True
            assert res.verification["status"] == "VERIFIED"

    finally:
        Path(img_path).unlink(missing_ok=True)
