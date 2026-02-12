import pytest


def test_imports():
    from reddiy import reddiy_bot, reddiy_prompts, reddiy_install
    from reddiy.integrations import fi_web
    assert True


def test_prompts_structure():
    from reddiy import reddiy_prompts
    assert hasattr(reddiy_prompts, "main_prompt")
    assert len(reddiy_prompts.main_prompt) > 1000
    assert "Reddiy" in reddiy_prompts.main_prompt
    assert "Manual Reddit Workflow Assistant" in reddiy_prompts.main_prompt
    assert "Flexus" in reddiy_prompts.main_prompt


def test_install_schema():
    from reddiy import reddiy_install
    schema = reddiy_install.REDDIY_SETUP_SCHEMA
    assert isinstance(schema, list)
    assert len(schema) == 4

    field_names = [field["bs_name"] for field in schema]
    assert "TARGET_SUBREDDITS" in field_names
    assert "BRAND_TONE" in field_names
    assert "ENGAGEMENT_GOAL" in field_names
    assert "WEEKLY_ENGAGEMENT_TARGET" in field_names

    assert "REDDIT_CLIENT_ID" not in field_names
    assert "REDDIT_CLIENT_SECRET" not in field_names
    assert "REDDIT_REFRESH_TOKEN" not in field_names


def test_tools_defined():
    from reddiy import reddiy_bot
    tools = reddiy_bot.TOOLS
    assert len(tools) > 0

    tool_names = [tool.name for tool in tools]
    assert "analyze_subreddit" in tool_names
    assert "draft_reply" in tool_names
    assert "analyze_thread" in tool_names
    assert "check_subreddit_rules" in tool_names
    assert "log_engagement" in tool_names
    assert "track_performance" in tool_names
    assert "suggest_subreddits" in tool_names
    assert "reddit_insights" in tool_names
    assert "web_scrape" in tool_names

    assert "reddit_api" not in tool_names
    assert "reddit_monitor" not in tool_names
    assert "reddit_reply" not in tool_names
    assert "reddit_approve_reply" not in tool_names


def test_keywords_defined():
    from reddiy import reddiy_bot
    keywords = reddiy_bot.RELEVANT_KEYWORDS
    assert isinstance(keywords, list)
    assert len(keywords) > 0
    assert "ai automation" in keywords
    assert "ai agents" in keywords


def test_tool_schemas():
    from reddiy import reddiy_bot

    analyze_tool = reddiy_bot.ANALYZE_SUBREDDIT_TOOL
    assert analyze_tool.strict == False
    assert analyze_tool.name == "analyze_subreddit"

    draft_tool = reddiy_bot.DRAFT_REPLY_TOOL
    assert draft_tool.strict == True
    assert "thread_url" in draft_tool.parameters["properties"]
    assert "style" in draft_tool.parameters["properties"]

    log_tool = reddiy_bot.LOG_ENGAGEMENT_TOOL
    assert log_tool.strict == True
    assert "thread_url" in log_tool.parameters["properties"]
    assert "comment_url" in log_tool.parameters["properties"]
    assert "reply_text" in log_tool.parameters["properties"]
    assert "style" in log_tool.parameters["properties"]


def test_web_integration_init():
    from reddiy.integrations import fi_web

    integration = fi_web.IntegrationWeb()
    assert integration is not None
    assert hasattr(integration, "called_by_model")
    assert hasattr(integration, "problems_other")


@pytest.mark.asyncio
async def test_web_integration_help():
    from reddiy.integrations import fi_web

    integration = fi_web.IntegrationWeb()

    class MockToolCall:
        pass

    result = await integration.called_by_model(MockToolCall(), {"op": "help"})
    assert isinstance(result, str)
    assert "fetch_thread" in result
    assert "search_subreddit" in result
    assert "get_rules" in result


@pytest.mark.asyncio
async def test_web_integration_fetch_thread():
    from reddiy.integrations import fi_web
    import json

    integration = fi_web.IntegrationWeb()

    class MockToolCall:
        pass

    result = await integration.called_by_model(
        MockToolCall(),
        {"op": "fetch_thread", "args": {"url": "https://reddit.com/r/startups/comments/abc123/test"}},
    )
    assert isinstance(result, str)
    assert "ERROR" not in result or "placeholder" in result.lower()


@pytest.mark.asyncio
async def test_web_integration_search_subreddit():
    from reddiy.integrations import fi_web
    import json

    integration = fi_web.IntegrationWeb()

    class MockToolCall:
        pass

    result = await integration.called_by_model(
        MockToolCall(),
        {"op": "search_subreddit", "args": {"subreddit": "startups", "limit": 10}},
    )
    assert isinstance(result, str)
    assert "ERROR" not in result or "placeholder" in result.lower()


@pytest.mark.asyncio
async def test_web_integration_get_rules():
    from reddiy.integrations import fi_web
    import json

    integration = fi_web.IntegrationWeb()

    class MockToolCall:
        pass

    result = await integration.called_by_model(
        MockToolCall(),
        {"op": "get_rules", "args": {"subreddit": "startups"}},
    )
    assert isinstance(result, str)
    assert "ERROR" not in result or "placeholder" in result.lower()


def test_version_updated():
    from reddiy import reddiy_bot, reddiy_install
    assert reddiy_bot.BOT_VERSION == "0.2.0"
    assert reddiy_install.BOT_VERSION == "0.2.0"


def test_no_reddit_api_imports():
    try:
        from reddiy.integrations import fi_reddit
        assert False, "fi_reddit should not exist"
    except ImportError:
        pass
