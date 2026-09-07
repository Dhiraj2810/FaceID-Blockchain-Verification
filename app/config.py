import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from pydantic_settings import BaseSettings
    from pydantic import ConfigDict

    class Settings(BaseSettings):
        model_config = ConfigDict(extra="ignore", env_file=".env")

        SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY", "")
        RPC_URL: str = os.getenv("RPC_URL", "")
        PRIVATE_KEY: str = os.getenv("PRIVATE_KEY", "")
        CONTRACT_ADDRESS: str = os.getenv("CONTRACT_ADDRESS", "")
        CHAIN_ID: int = int(os.getenv("CHAIN_ID", "11155111"))

        FACE_MATCH_THRESHOLD: float = float(os.getenv("FACE_MATCH_THRESHOLD", "0.70"))
        FACE_DET_SIZE: int = int(os.getenv("FACE_DET_SIZE", "640"))
        FACE_DET_THRESHOLD: float = float(os.getenv("FACE_DET_THRESHOLD", "0.25"))
        MAX_CANDIDATES: int = int(os.getenv("MAX_CANDIDATES", "10"))
        REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "45"))
        MAX_IMAGE_SIZE_MB: int = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))

        INPUT_DIR: Path = BASE_DIR / "input"
        RESULTS_DIR: Path = BASE_DIR / "results"

        @property
        def NETWORK_NAME(self) -> str:
            return "Ethereum Sepolia" if self.RPC_URL and "sepolia" in self.RPC_URL.lower() else "Web3 Simulator"

except ImportError:
    # Manual fallback settings object if pydantic-settings is not yet installed
    class Settings:
        def __init__(self):
            self.SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")
            self.RPC_URL = os.getenv("RPC_URL", "")
            self.PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
            self.CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "")
            self.CHAIN_ID = int(os.getenv("CHAIN_ID", "11155111"))
            self.FACE_MATCH_THRESHOLD = float(os.getenv("FACE_MATCH_THRESHOLD", "0.70"))
            self.FACE_DET_SIZE = int(os.getenv("FACE_DET_SIZE", "640"))
            self.FACE_DET_THRESHOLD = float(os.getenv("FACE_DET_THRESHOLD", "0.25"))
            self.MAX_CANDIDATES = int(os.getenv("MAX_CANDIDATES", "10"))
            self.REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "45"))
            self.MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", "10"))
            self.INPUT_DIR = BASE_DIR / "input"
            self.RESULTS_DIR = BASE_DIR / "results"

        @property
        def NETWORK_NAME(self) -> str:
            return "Ethereum Sepolia" if self.RPC_URL and "sepolia" in self.RPC_URL.lower() else "Web3 Simulator"


settings = Settings()

# Ensure required directories exist
settings.INPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
