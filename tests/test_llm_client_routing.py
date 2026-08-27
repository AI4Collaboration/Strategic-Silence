from info_marketplace.llm_client import is_deepseek, is_openrouter, model_provenance


def test_slash_qualified_models_route_to_openrouter():
    assert is_openrouter("stealth/ox-alpha")
    assert not is_deepseek("stealth/ox-alpha")
    assert model_provenance("stealth/ox-alpha") == {
        "provider": "openrouter",
        "checkpoint": "stealth/ox-alpha",
        "revision": "api",
    }


def test_deepseek_namespace_model_routes_to_openrouter():
    assert is_openrouter("deepseek/deepseek-v4-flash")
    assert not is_deepseek("deepseek/deepseek-v4-flash")
    assert model_provenance("deepseek/deepseek-v4-flash")["provider"] == "openrouter"


def test_existing_provider_routes_remain_distinct():
    assert is_deepseek("deepseek-chat")
    assert not is_openrouter("deepseek-chat")
    assert not is_openrouter("gpt-5.4-mini")
