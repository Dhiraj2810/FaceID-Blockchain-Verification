import pytest
from app.search.serpapi_lens import SerpApiLensSearcher
from app.evidence.models import CandidateResult


def test_serpapi_response_parser():
    mock_data = {
        "visual_matches": [
            {
                "title": "Post Match 1",
                "link": "https://instagram.com/p/match1",
                "thumbnail": "https://instagram.com/p/thumb1.jpg"
            },
            {
                "title": "Post Match 2 (Duplicate Link)",
                "link": "https://instagram.com/p/match1",
                "thumbnail": "https://instagram.com/p/thumb2.jpg"
            },
            {
                "title": "Post Match 3",
                "link": "https://twitter.com/user/status/12345",
                "thumbnail": "https://twitter.com/thumb3.jpg"
            }
        ]
    }

    searcher = SerpApiLensSearcher(api_key="test_key")
    candidates = searcher.parse_response(mock_data)

    assert len(candidates) == 2  # Deduplicated from 3 to 2
    assert candidates[0].title == "Post Match 1"
    assert candidates[0].url == "https://instagram.com/p/match1"
    assert candidates[1].url == "https://twitter.com/user/status/12345"


def test_serpapi_empty_matches():
    mock_data = {"visual_matches": []}
    searcher = SerpApiLensSearcher(api_key="test_key")
    candidates = searcher.parse_response(mock_data)

    assert candidates == []
