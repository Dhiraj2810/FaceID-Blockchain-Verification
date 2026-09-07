from datetime import datetime, timezone
from typing import Optional, List, Any
from pydantic import BaseModel, Field


class FaceDetectionResult(BaseModel):
    face_detected: bool
    face_count: int
    embedding_generated: bool
    bbox: Optional[List[int]] = None


class CandidateResult(BaseModel):
    title: str
    url: str
    thumbnail_url: Optional[str] = None
    source: str = "Google Lens"


class CandidateMatch(BaseModel):
    matched: bool
    similarity: float
    candidate_url: str
    candidate_title: str
    candidate_image: str


class EvidenceRecord(BaseModel):
    source_url: str
    title: str
    search_provider: str = "Google Lens"
    face_similarity: float
    image_path: str
    discovered_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class BlockchainRecord(BaseModel):
    transaction_hash: str
    record_id: int
    contract_address: str
    network: str = "Sepolia"
    on_chain_hash: str


class VerificationResult(BaseModel):
    verified: bool
    local_hash: str
    on_chain_hash: str
    status: str  # "VERIFIED" or "TAMPERED"


class PipelineResult(BaseModel):
    status: str = "success"
    message: Optional[str] = None
    face: Optional[dict] = None
    search: Optional[dict] = None
    match: Optional[dict] = None
    blockchain: Optional[dict] = None
    verification: Optional[dict] = None
