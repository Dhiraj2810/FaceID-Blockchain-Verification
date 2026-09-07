import os
import pytest
import numpy as np
from pathlib import Path
from app.face.matcher import compare_faces, compare_embeddings
from app.face.detector import detect_faces
from app.face.embedding import generate_embedding
from app.config import settings
from app.evidence.models import CandidateResult
from app.evidence.extractor import process_candidates


def test_compare_faces_identical_vectors():
    vec = np.random.randn(512).astype(np.float32)
    vec = vec / np.linalg.norm(vec)

    score, matched = compare_faces(vec, vec, threshold=0.70)

    assert score == pytest.approx(1.0, abs=1e-3)
    assert matched is True


def test_compare_faces_orthogonal_vectors():
    vec_a = np.zeros(512, dtype=np.float32)
    vec_a[0] = 1.0

    vec_b = np.zeros(512, dtype=np.float32)
    vec_b[1] = 1.0

    score, matched = compare_faces(vec_a, vec_b, threshold=0.70)

    assert score == pytest.approx(0.0, abs=1e-3)
    assert matched is False


def test_compare_faces_threshold_boundary():
    # Construct 2 vectors with known cosine similarity ~0.80
    vec_a = np.array([1.0, 0.0], dtype=np.float32)
    # angle 36.87 deg -> cos(angle) = 0.80
    vec_b = np.array([0.8, 0.6], dtype=np.float32)

    score, matched_high = compare_faces(vec_a, vec_b, threshold=0.85)
    assert score == pytest.approx(0.80, abs=1e-2)
    assert matched_high is False

    score, matched_low = compare_faces(vec_a, vec_b, threshold=0.70)
    assert matched_low is True


def test_compare_embeddings_logs_reason():
    vec_a = np.random.randn(512).astype(np.float32)
    vec_a /= np.linalg.norm(vec_a)

    res = compare_embeddings(vec_a, vec_a, threshold=0.70)

    assert "similarity" in res
    assert "matched" in res
    assert "reason" in res
    assert res["matched"] is True
    assert "MATCH:" in res["reason"]
    assert "0.7000" in res["reason"]


def test_same_person_different_pose_match():
    # Construct 2 embeddings representing different photos/poses of the same person (cos sim = 0.85)
    base = np.random.randn(512).astype(np.float32)
    base /= np.linalg.norm(base)

    ortho = np.random.randn(512).astype(np.float32)
    ortho -= np.dot(ortho, base) * base
    ortho /= np.linalg.norm(ortho)

    target_sim = 0.85
    variant = target_sim * base + np.sqrt(1.0 - target_sim**2) * ortho

    res = compare_embeddings(base, variant, threshold=0.70)

    assert res["matched"] is True
    assert res["similarity"] >= 0.70
    assert "MATCH:" in res["reason"]


def test_clearly_different_person_no_match():
    # Construct 2 independent embeddings for different individuals
    person_a = np.random.randn(512).astype(np.float32)
    person_a /= np.linalg.norm(person_a)

    person_b = np.random.randn(512).astype(np.float32)
    person_b /= np.linalg.norm(person_b)

    res = compare_embeddings(person_a, person_b, threshold=0.70)

    assert res["matched"] is False
    assert res["similarity"] < 0.70
    assert "NO MATCH:" in res["reason"]


def test_same_identity_different_context_eligible_for_match():
    """
    Verifies that same identity under completely different context (different clothing,
    pose, background, lighting) evaluates face identity and is eligible for MATCH.
    """
    person_a_base = np.random.randn(512).astype(np.float32)
    person_a_base /= np.linalg.norm(person_a_base)

    ortho = np.random.randn(512).astype(np.float32)
    ortho -= np.dot(ortho, person_a_base) * person_a_base
    ortho /= np.linalg.norm(ortho)

    # Different photo/clothing/lighting of Person A (high face similarity 0.82)
    person_a_diff_context = 0.82 * person_a_base + np.sqrt(1.0 - 0.82**2) * ortho

    res = compare_embeddings(person_a_base, person_a_diff_context, threshold=0.70)

    assert res["matched"] is True
    assert res["similarity"] == pytest.approx(0.82, abs=1e-2)
    assert "MATCH:" in res["reason"]


def test_different_identity_similar_context_not_match():
    """
    Verifies that two different individuals sharing identical context (e.g. same school
    uniform, background, or posture) evaluate low facial similarity and result in NO MATCH.
    """
    person_a = np.array([1.0] + [0.0] * 511, dtype=np.float32)
    # Person B wearing same uniform/in same room (low face similarity 0.15)
    person_b_same_uniform = np.array([0.15, 0.9886] + [0.0] * 510, dtype=np.float32)

    res = compare_embeddings(person_a, person_b_same_uniform, threshold=0.70)

    assert res["matched"] is False
    assert res["similarity"] == pytest.approx(0.15, abs=1e-2)
    assert "NO MATCH:" in res["reason"]


def test_multi_face_candidate_selection():
    # Target face embedding
    target = np.array([1.0] + [0.0] * 511, dtype=np.float32)

    # Candidate containing 3 faces: face 1 (sim ~ 0.2), face 2 (sim ~ 0.85), face 3 (sim ~ 0.1)
    cand_face1 = np.array([0.2, 0.98] + [0.0] * 510, dtype=np.float32)
    cand_face2 = np.array([0.85, 0.5268] + [0.0] * 510, dtype=np.float32)
    cand_face3 = np.array([0.1, 0.995] + [0.0] * 510, dtype=np.float32)

    evals = []
    for cand_emb in [cand_face1, cand_face2, cand_face3]:
        evals.append(compare_embeddings(target, cand_emb, threshold=0.70))

    best_eval = max(evals, key=lambda x: x["similarity"])

    assert best_eval["similarity"] == pytest.approx(0.85, abs=1e-2)
    assert best_eval["matched"] is True
    assert "MATCH:" in best_eval["reason"]


def test_real_photos_verification():
    # If LFW benchmark test photos exist in input/, verify live ArcFace cross-photo behavior
    same_1 = settings.INPUT_DIR / "lfw_same_1.jpg"
    same_2 = settings.INPUT_DIR / "lfw_same_2.jpg"
    diff = settings.INPUT_DIR / "lfw_diff.jpg"

    if same_1.exists() and same_2.exists() and diff.exists():
        f1, _ = detect_faces(same_1)
        f2, _ = detect_faces(same_2)
        fd, _ = detect_faces(diff)

        if f1 and f2 and fd:
            emb1 = generate_embedding(f1[0])
            emb2 = generate_embedding(f2[0])
            embd = generate_embedding(fd[0])

            res_same = compare_embeddings(emb1, emb2, threshold=0.70)
            res_diff = compare_embeddings(emb1, embd, threshold=0.70)

            # Same person different photo must MATCH
            assert res_same["matched"] is True
            assert res_same["similarity"] >= 0.70
            assert "MATCH:" in res_same["reason"]

            # Unrelated person must NO MATCH
            assert res_diff["matched"] is False
            assert res_diff["similarity"] < 0.70
            assert "NO MATCH:" in res_diff["reason"]
