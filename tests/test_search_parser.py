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


def test_social_media_domain_filtering_and_capping():
    from app.search.serpapi_lens import is_social_media_url
    from app.config import settings

    assert is_social_media_url("https://instagram.com/p/123") is True
    assert is_social_media_url("https://x.com/user/status/456") is True
    assert is_social_media_url("https://randomwebsite.com/article") is False

    mock_matches = []
    # Add 15 generic matches
    for i in range(15):
        mock_matches.append({
            "title": f"Generic Web Site {i}",
            "link": f"https://generic-blog-{i}.com/page"
        })
    # Add 3 social media matches
    mock_matches.append({"title": "Insta Post", "link": "https://instagram.com/p/test"})
    mock_matches.append({"title": "Tweet Post", "link": "https://twitter.com/user/status/123"})
    mock_matches.append({"title": "Reddit Post", "link": "https://reddit.com/r/pics/123"})

    mock_data = {"visual_matches": mock_matches}
    searcher = SerpApiLensSearcher(api_key="test_key")
    candidates = searcher.parse_response(mock_data)

    # Must be capped at MAX_CANDIDATES (10)
    assert len(candidates) <= settings.MAX_CANDIDATES
    # Social media candidates must be prioritized at top of list
    social_urls = [c.url for c in candidates if is_social_media_url(c.url)]
    assert len(social_urls) == 3
    assert candidates[0].url == "https://instagram.com/p/test"

