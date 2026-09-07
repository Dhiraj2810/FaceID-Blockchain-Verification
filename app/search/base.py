from abc import ABC, abstractmethod
from typing import List
from app.evidence.models import CandidateResult


class BaseReverseImageSearcher(ABC):
    """
    Abstract Base Class for Reverse Image Search services.
    Allows easy swapping of search providers (SerpApi Google Lens, TinEye, etc.)
    """

    @abstractmethod
    def search(self, image_path: str) -> List[CandidateResult]:
        """
        Executes reverse image search for the given local image file path.
        Returns a list of normalized CandidateResult objects.
        """
        pass
