from audience_discovery.search.mock_provider import MockSearchProvider
from audience_discovery.search.serpapi_provider import SERPAPI_ENDPOINT, SerpAPIProvider
from audience_discovery.search.youtube_provider import YouTubeProvider


class FakeResponse:
    def __init__(self, data, status_code: int = 200) -> None:
        self._data = data
        self.status_code = status_code

    def json(self):
        return self._data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(f"status {self.status_code}")


class FakeSerpAPIClient:
    def __init__(self, responses) -> None:
        self.responses = list(responses)
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return self.responses.pop(0)


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


def test_serpapi_provider_missing_key_returns_empty() -> None:
    provider = SerpAPIProvider(api_key="", rate_limit_seconds=0)

    assert provider.search("biohacking newsletter sponsor", "biohacking_newsletters") == []
    assert "SERPAPI_API_KEY" in (provider.warning or "")


def test_serpapi_provider_paginates_and_dedupes_domains() -> None:
    client = FakeSerpAPIClient(
        [
            FakeResponse(
                {
                    "organic_results": [
                        {
                            "title": "Biohacking Sponsor Page",
                            "link": "https://alpha.example/advertise",
                            "snippet": "Advertise in our biohacking newsletter.",
                        },
                        {
                            "title": "Duplicate Domain",
                            "link": "https://alpha.example/media-kit",
                            "snippet": "Media kit.",
                        },
                    ]
                }
            ),
            FakeResponse(
                {
                    "organic_results": [
                        {
                            "title": "Second Domain",
                            "link": "https://beta.example/sponsor",
                            "snippet": "Sponsor our longevity audience.",
                        },
                        {
                            "title": "Third Domain",
                            "link": "https://gamma.example/contact",
                            "snippet": "Business inquiries.",
                        },
                    ]
                }
            ),
        ]
    )
    provider = SerpAPIProvider(api_key="key", client=client, page_size=2, rate_limit_seconds=0)

    results = provider.search("biohacking newsletter sponsor", "biohacking_newsletters", limit=3)

    assert [result.domain for result in results] == ["alpha.example", "beta.example", "gamma.example"]
    assert results[0].title == "Biohacking Sponsor Page"
    assert results[0].url == "https://alpha.example/advertise"
    assert results[0].snippet == "Advertise in our biohacking newsletter."
    assert results[0].source == "serpapi"
    assert client.calls[0]["url"] == SERPAPI_ENDPOINT
    assert client.calls[0]["params"]["engine"] == "google"
    assert client.calls[0]["params"]["q"] == "biohacking newsletter sponsor"
    assert client.calls[0]["params"]["start"] == 0
    assert client.calls[1]["params"]["start"] == 2


def test_serpapi_provider_retries_transient_failures() -> None:
    client = FakeSerpAPIClient(
        [
            FakeResponse({}, status_code=429),
            FakeResponse(
                {
                    "organic_results": [
                        {
                            "title": "Recovered",
                            "link": "https://recovered.example",
                            "snippet": "Sponsor page.",
                        }
                    ]
                }
            ),
        ]
    )
    provider = SerpAPIProvider(api_key="key", client=client, rate_limit_seconds=0, max_retries=1)

    results = provider.search("fitness science newsletter sponsor", "fitness_science_communities", limit=1)

    assert len(client.calls) == 2
    assert results[0].domain == "recovered.example"
