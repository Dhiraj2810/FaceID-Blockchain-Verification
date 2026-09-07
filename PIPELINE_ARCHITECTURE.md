# Face Identification & Blockchain Verification Pipeline Architecture

This document provides a detailed breakdown of how the **Face Identification & Blockchain Verification Pipeline** works under the hood.

---

## High-Level Pipeline Flowchart

```text
[1/7] Input Image Loading & Format Normalization
                    ↓
[2/7] Biometric Face Detection (InsightFace SCRFD + 7 Multi-Scale Strategies)
                    ↓
[3/7] ArcFace 512-Dimensional Vector Embedding Generation
                    ↓
[4/7] Dual-Strategy Reverse Image Search (SerpApi Google Lens + Public CDN)
                    ↓
[5/7] Candidate Retrieval & Cosine Similarity Verification (Threshold >= 0.70)
                    ↓
[6/7] Cryptographic SHA-256 Fingerprinting & Ethereum Web3 Registration
                    ↓
[7/7] On-Chain Re-Verification & Byte-Level Tamper Detection
```

---

## Detailed 7-Stage Pipeline Breakdown

### Stage 1: Input Image Loading & Format Normalization
* **File Location**: [`app/face/detector.py`](file:///d:/HHg%20task%203%20%283%29/HHg%20task%203/app/face/detector.py#L50-L116)
* **Input**: Local file path (JPG, PNG, WEBP), HTTP/HTTPS image URL, or raw NumPy array.
* **Process**:
  1. If a web URL is provided, the pipeline safely downloads the raw byte stream into `input/temp_url_input.jpg`.
  2. Decodes image into OpenCV `BGR` uint8 format.
  3. Handles channel conversions automatically:
     * Grayscale (1 channel) $\to$ `COLOR_GRAY2BGR`
     * BGRA (4 channels) $\to$ `COLOR_BGRA2BGR`
  4. Returns C-contiguous `uint8` image array and image metadata (`width`, `height`, `channels`).

---

### Stage 2: Biometric Face Detection
* **File Location**: [`app/face/detector.py`](file:///d:/HHg%20task%203%20%283%29/HHg%20task%203/app/face/detector.py#L118-L348)
* **Model Pack**: InsightFace `buffalo_l` (SCRFD Face Detector).
* **Robust 7-Level Multi-Scale Detection Strategy**:
  To guarantee face detection across ultra-high-resolution DSLR photos, low-resolution web thumbnails, side profiles, or poorly lit images, the system executes an adaptive fallback cascade:
  1. **Ultra-High Resolution Downscaling**: If maximum dimension $> 1920\text{px}$, downscale to $1280\text{px}$ max side.
  2. **Native Resolution Scan**: Standard evaluation on full input image.
  3. **Square Letterbox Canvas (Attempt 2b)**: Pads non-square images into a square canvas to eliminate aspect ratio stretching in SCRFD anchors.
  4. **Mid-Resolution Downscaling**: Downscales to $800\text{px}$ max side for small face feature extraction.
  5. **Controlled Upscaling (1.5x / 2.0x)**: Upscales small cropped inputs using cubic interpolation.
  6. **Adaptive Confidence Thresholding**: Dynamically lowers detector threshold to `det_thresh=0.15`.
  7. **CLAHE Enhancement + Haar Cascade Fallback**: Contrast Limited Adaptive Histogram Equalization in `YCrCb` color space combined with OpenCV Haar Cascade fallback.
* **Strict Validation Rule**: Requires **exactly 1 primary face** in target input. If 0 faces or multiple faces are found, pipeline halts cleanly with diagnostic error logs.

---

### Stage 3: ArcFace 512-D Embedding Generation
* **File Location**: [`app/face/embedding.py`](file:///d:/HHg%20task%203%20%283%29/HHg%20task%203/app/face/embedding.py#L5-L33)
* **Model**: ArcFace (Additive Angular Margin Loss Deep Convolutional Neural Network).
* **Process**:
  1. Extracts 512 facial feature landmarks from the aligned face crop.
  2. Generates a 512-dimensional floating-point feature vector $\mathbf{e} \in \mathbb{R}^{512}$.
  3. Performs **$L_2$ Normalization**:
     $$\hat{\mathbf{e}} = \frac{\mathbf{e}}{\|\mathbf{e}\|_2}$$
  4. Zero-fallback enforcement: Synthetic or dummy vector fallbacks are strictly disabled to prevent non-biometric security bypass.

---

### Stage 4: Dual-Strategy Reverse Image Search (SerpApi Google Lens)
* **File Location**: [`app/search/serpapi_lens.py`](file:///d:/HHg%20task%203%20%283%29/HHg%20task%203/app/search/serpapi_lens.py#L11-L216)
* **Dual-Search Strategy**:
  1. **Identity-Focused Face Crop Search**: Crops detected face with a $20\%$ proportional margin (captures full jawline and hair while excluding clothing/background distractions), uploads to CDN (Catbox / tmpfiles), and queries SerpApi Google Lens.
  2. **Full Scene Fallback Search**: Executes full-image visual search if face crop search returns limited items.
* **Response Parsing & Aggregation**:
  * Extracts candidate web links from 6 SerpApi JSON categories: `visual_matches`, `exact_matches`, `related_content`, `organic_results`, `images_results`, and `knowledge_graph`.
  * Deduplicates candidates by unique page URL.
  * Sanitizes API key and saves raw response audit log to `results/search_raw_<timestamp>.json`.

---

### Stage 5: Candidate Retrieval & Cosine Similarity Verification
* **File Location**: [`app/evidence/extractor.py`](file:///d:/HHg%20task%203%20%283%29/HHg%20task%203/app/evidence/extractor.py#L16-L189) & [`app/face/matcher.py`](file:///d:/HHg%20task%203%20%283%29/HHg%20task%203/app/face/matcher.py#L6-L50)
* **Process**:
  1. Iterates through discovered web candidates and downloads candidate image thumbnails with safe resource limits ($10\text{MB}$ max size, $15\text{s}$ timeout).
  2. Detects all faces present in candidate web images.
  3. Generates 512-d ArcFace embeddings for each candidate face.
  4. Calculates **Cosine Similarity** against original target embedding $\hat{\mathbf{e}}_{\text{target}}$:
     $$\text{Similarity}(\hat{\mathbf{e}}_{\text{target}}, \hat{\mathbf{e}}_{\text{cand}}) = \frac{\hat{\mathbf{e}}_{\text{target}} \cdot \hat{\mathbf{e}}_{\text{cand}}}{\|\hat{\mathbf{e}}_{\text{target}}\|_2 \|\hat{\mathbf{e}}_{\text{cand}}\|_2}$$
  5. **Threshold Evaluation**: Checks if score meets or exceeds `FACE_MATCH_THRESHOLD` (Default: `0.70`).
  6. **Evidence Preservation**: Selects highest-scoring matching candidate and saves evidence file as `results/matched_<timestamp>.jpg` retaining original raw byte sequence.

---

### Stage 6: Cryptographic SHA-256 Fingerprinting & Web3 Registration
* **File Locations**: [`app/crypto/hashing.py`](file:///d:/HHg%20task%203%20%283%29/HHg%20task%203/app/crypto/hashing.py) & [`app/blockchain/verifier.py`](file:///d:/HHg%20task%203%20%283%29/HHg%20task%203/app/blockchain/verifier.py)
* **Smart Contract**: `contracts/FaceVerificationRegistry.sol` on Ethereum Sepolia Testnet.
* **Process**:
  1. Computes SHA-256 cryptographic fingerprint of the saved evidence image file:
     $$\text{Hash} = \text{SHA-256}(\text{evidence\_file\_bytes})$$
  2. Converts 64-character hex hash string to Solidity `bytes32`.
  3. Invokes Smart Contract function:
     ```solidity
     recordVerification(bytes32 _contentHash, string memory _sourceUrl)
     ```
  4. Returns Web3 record metadata containing `transaction_hash`, `record_id`, `contract_address`, and `network`.
  5. *Note: Includes automatic fallback to local simulated Web3 node if testnet RPC is unavailable.*

---

### Stage 7: On-Chain Re-Verification & Tamper Detection
* **File Location**: [`app/blockchain/verifier.py`](file:///d:/HHg%20task%203%20%283%29/HHg%20task%203/app/blockchain/verifier.py) & [`app/main.py`](file:///d:/HHg%20task%203%20%283%29/HHg%20task%203/app/main.py#L85-L139)
* **Process**:
  1. Queries smart contract method `getRecord(record_id)` to retrieve immutable registered `content_hash`.
  2. Re-computes SHA-256 hash of local evidence file on disk.
  3. Compares `Hash_local` vs `Hash_on_chain`:
     * If $\text{Hash}_{\text{local}} == \text{Hash}_{\text{on-chain}} \implies$ **VERIFIED** ✅
     * If $\text{Hash}_{\text{local}} \neq \text{Hash}_{\text{on-chain}} \implies$ **TAMPER DETECTED** ❌
  4. Any byte-level alteration to the evidence image triggers immediate tamper alert.

---

## REST API & Web Dashboard Integration

| Component | Port | Endpoint / Purpose |
| :--- | :--- | :--- |
| **FastAPI Backend** | `8000` | `POST /verify` (Runs 7-stage pipeline)<br>`POST /tamper-test` (Simulates tamper check)<br>`DELETE /records/{filename}` (Removes evidence record) |
| **React + Vite Dashboard** | `5173` | Interactive visual dashboard for image upload, real-time pipeline status, face similarity metrics, and Web3 proof inspector. |

---

## Data Privacy & Biometric Security
1. **No On-Chain Biometrics**: Raw 512-d biometric face vectors are stored strictly in-memory during processing and are **never** logged, saved to disk, or sent to the blockchain.
2. **Cryptographic Proof**: Only SHA-256 content hashes (`bytes32`) and public source URLs are recorded on-chain.
