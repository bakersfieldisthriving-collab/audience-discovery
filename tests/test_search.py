from audience_discovery.search.mock_provider import MockSearchProvider
from audience_discovery.search.youtube_provider import YouTubeProvider


def test_mock_search_provider_is_deterministic() -> None:
    provider = MockSearchProvider()

    first = provider.search("biohacking newsletter sponsor", "biohacking_newsletters", 2)
    second = provider.search("biohacking newsletter sponsor", "biohacking_newsletters", 2)

    assert first == second
    assert len(first) == 2
    assert first[0].source == "mock"


def test_youtube_provider_missing_key_returns_empty() -> None:
    provider = YouTubeProvider(api_key="")

    assert provider.search("longevity YouTube channel newsletter", "youtubers_with_email_lists") == []
    assert "YOUTUBE_API_KEY" in (provider.warning or "")
