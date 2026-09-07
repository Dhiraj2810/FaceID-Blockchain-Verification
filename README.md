# Face Identification & Blockchain Verification Pipeline

Production-quality prototype for **HH Goa 2026 Shortlisting Task 3: Face Identification & Blockchain Verification**.

This system implements an automated end-to-end pipeline that detects faces from input images, performs runtime reverse image web search (via SerpApi Google Lens abstraction), independently verifies facial similarity using ArcFace embeddings, extracts cryptographic SHA-256 fingerprints, registers evidence on an Ethereum Sepolia Smart Contract via Web3, and performs on-chain re-verification with live tamper detection.

---

## Architecture

```text
Input Face Image
      ↓
Face Detection (InsightFace / SCRFD)
      ↓
ArcFace 512-d Embedding Generation
      ↓
Google Lens Reverse Image Search (SerpApi)
      ↓
Candidate Images & Web Posts
      ↓
Independent Face Verification (Cosine Similarity >= 0.70)
      ↓
Select Best Matching Candidate & Save Evidence File
      ↓
Cryptographic SHA-256 Content Fingerprint (Hex & Bytes32)
      ↓
Ethereum Smart Contract Registration (FaceVerificationRegistry.sol)
      ↓
Web3 On-Chain Record Retrieval
      ↓
Local Hash Recalculation vs On-Chain Hash
      ↓
VERIFIED / TAMPERED
```

---

## Tech Stack

* **Backend**: Python 3.11+, FastAPI, Pydantic, python-dotenv
* **Computer Vision & AI**: InsightFace, ArcFace Embeddings, SCRFD Face Detector, ONNX Runtime, OpenCV, NumPy
* **Reverse Image Search**: SerpApi Google Lens Engine abstraction (`BaseReverseImageSearcher`)
* **Blockchain**: Ethereum Sepolia Testnet, Web3.py, Solidity ^0.8.20 (`FaceVerificationRegistry.sol`)
* **Hashing**: SHA-256 (Python `hashlib`)
* **Testing**: pytest

---

## Project Structure

```text
face-chain-verifier/
│
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI REST API endpoint (POST /verify)
│   ├── config.py                   # Pydantic configuration & environment settings
│   │
│   ├── face/                       # Computer vision & biometric embedding engine
│   │   ├── __init__.py
│   │   ├── detector.py             # Face detection (SCRFD / InsightFace)
│   │   ├── embedding.py            # 512-d ArcFace feature embeddings
│   │   └── matcher.py              # Cosine similarity matching & threshold evaluation
│   │
│   ├── search/                     # Reverse image web search abstraction
│   │   ├── __init__.py
│   │   ├── base.py                 # Abstract Base Class for search providers
│   │   └── serpapi_lens.py         # SerpApi Google Lens client & raw response logger
│   │
│   ├── evidence/                   # Evidence downloading & extraction
│   │   ├── __init__.py
│   │   ├── downloader.py           # Secure HTTP image downloader & MIME validator
│   │   ├── extractor.py            # Evidence extraction & candidate verification
│   │   └── models.py               # Pydantic data schemas
│   │
│   ├── blockchain/                 # Web3 & Smart Contract integration
│   │   ├── __init__.py
│   │   ├── contract.py             # Contract ABI, Web3 transaction builder & simulation
│   │   └── verifier.py             # Blockchain Service & on-chain re-verifier
│   │
│   ├── crypto/                     # Cryptographic fingerprinting
│   │   ├── __init__.py
│   │   └── hashing.py              # File SHA-256 & Solidity bytes32 formatter
│   │
│   └── pipeline/                   # Core orchestrator
│       ├── __init__.py
│       └── orchestrator.py         # 7-step pipeline execution engine
│
├── contracts/
│   └── FaceVerificationRegistry.sol # Solidity ^0.8.20 Smart Contract
│
├── scripts/
│   ├── deploy.py                   # Contract deployment script to Sepolia
│   └── verify_transaction.py       # On-chain record inspection tool
│
├── tests/                          # Automated pytest unit & integration tests
│   ├── test_face_matching.py
│   ├── test_hashing.py
│   ├── test_search_parser.py
│   └── test_pipeline.py
│
├── input/                          # Input images directory
│   └── .gitkeep
│
├── results/                        # Matched evidence & raw search response logs
│   └── .gitkeep
│
├── .env.example                    # Environment variables template
├── .gitignore
├── requirements.txt
├── README.md
└── run.py                          # CLI runner & Tamper Demonstration Tool
```

---

## Installation & Setup

1. **Clone Repository & Install Dependencies**:
   ```bash
   git clone <repository_url>
   cd face-chain-verifier
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

3. **Configure Settings in `.env`**:
   ```env
   # Reverse Image Search Configuration
   SERPAPI_API_KEY=your_serpapi_key_here

   # Blockchain Configuration (Sepolia Testnet)
   RPC_URL=https://eth-sepolia.g.alchemy.com/v2/your_alchemy_key
   PRIVATE_KEY=0xyour_private_key_here
   CONTRACT_ADDRESS=0x0000000000000000000000000000000000000000
   CHAIN_ID=11155111

   # Pipeline Parameters
   FACE_MATCH_THRESHOLD=0.70
   MAX_CANDIDATES=10
   REQUEST_TIMEOUT=15
   MAX_IMAGE_SIZE_MB=10
   ```

---

## Blockchain Setup & Contract Deployment

1. **Obtain Sepolia Testnet ETH**:
   Acquire testnet ETH from a Sepolia Faucet (e.g. Alchemy or Infura Sepolia Faucet) for your wallet address.

2. **Deploy Smart Contract**:
   Run the deployment script:
   ```bash
   python scripts/deploy.py
   ```
   Copy the deployed contract address output and update `CONTRACT_ADDRESS` in `.env`.

*Note: If no private key or RPC URL is configured, the system automatically falls back to an in-memory Web3 blockchain state simulator, allowing offline demonstration and automated testing.*

---

## Running the Pipeline

### 1. Standard Pipeline Execution
To execute the pipeline against an input face image:

```bash
python run.py --image input/test.jpg
```

**Example Terminal Output**:
```text
==================================================
 FACE IDENTIFICATION & BLOCKCHAIN VERIFIER
==================================================

[1/7] Loading image
      ✓ input image loaded

[2/7] Detecting face
      ✓ 1 face detected

[3/7] Generating face embedding
      ✓ ArcFace embedding generated

[4/7] Performing reverse image search
      ✓ search completed
      ✓ 8 candidates discovered

[5/7] Verifying candidates
      Candidate 1 → 0.41
      Candidate 2 → 0.56
      Candidate 3 → 0.89 ✓ MATCH

[6/7] Registering evidence
      ✓ SHA-256 generated (9f8a4c21...)
      ✓ Blockchain transaction submitted

[7/7] Re-verifying
      Local Hash : 9f8a4c21...
      Chain Hash : 9f8a4c21...

      ✅ BLOCKCHAIN VERIFIED

Transaction:
0x8f42d9...
==================================================
```

### 2. Live Tamper Detection Demonstration
To demonstrate how blockchain tamper-proofing detects byte-level evidence manipulation:

```bash
python run.py --demo-tamper
```

**Output**:
```text
==================================================
 TAMPER DEMONSTRATION MODE
==================================================
Modifying evidence file: results/matched_1741219200.jpg

Original Hash : 9f8a4c21...
Modified Hash : 3a7b1e89...
On-Chain Hash : 9f8a4c21...

❌ TAMPER DETECTED: Content fingerprint no longer matches Blockchain record!
==================================================
```

---

## REST API (FastAPI)

Start the API server:
```bash
uvicorn app.main:app --reload
```

### Endpoint: `POST /verify`
Upload an image via `multipart/form-data`:

```bash
curl -X POST "http://127.0.0.1:8000/verify" \
  -F "image=@input/test.jpg"
```

**JSON Response**:
```json
{
  "status": "success",
  "face": {
    "detected": true,
    "count": 1
  },
  "search": {
    "provider": "Google Lens",
    "candidates_found": 8
  },
  "match": {
    "found": true,
    "similarity": 0.89,
    "source_url": "https://example.com/posts/discovered-match",
    "evidence_image": "results/matched_1741219200.jpg"
  },
  "blockchain": {
    "registered": true,
    "hash": "9f8a4c21...",
    "transaction_hash": "0x8f42d9...",
    "record_id": 0,
    "network": "Sepolia"
  },
  "verification": {
    "verified": true,
    "status": "VERIFIED"
  }
}
```

---

## Running Unit & Integration Tests

Run the full pytest suite:
```bash
pytest tests/ -v
```

---

## Privacy & Security Design

1. **Biometric Privacy**: Raw 512-d biometric face embeddings are processed strictly in memory and are **never** written to log files, disk, or uploaded to the blockchain.
2. **Cryptographic Fingerprinting**: Only the cryptographic SHA-256 content fingerprint (`bytes32`) and public source metadata are stored on-chain.
3. **Download Safety**: Downloader enforces file size caps (`10MB`), strict MIME type filtering (`JPEG/PNG/WEBP`), connection timeouts, and decodes images safely without executing content.
4. **Authorized Demonstration**: Designed exclusively for authorized, consented verification of public web images.

---

## Limitations

* **Reverse Image Search**: Search engines index candidate web pages based on visual feature matching; candidates must be independently verified via face recognition.
* **Face Similarity**: Face recognition similarity scores are probabilistic confidence measures (calibrated via `FACE_MATCH_THRESHOLD=0.70`).
* **Blockchain Proof**: Blockchain registration proves the un-tampered cryptographic integrity of discovered evidence since the moment of registration.
