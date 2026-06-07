from audience_discovery.config import load_app_config


def test_load_app_config() -> None:
    config = load_app_config()

    assert "longevity_communities" in config.categories
    assert "longevity community sponsor" in config.categories["longevity_communities"].seed_queries
    assert config.scoring_weights["audience_relevance"] == 30
