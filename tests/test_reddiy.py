import pytest
import os
import json


def test_imports():
    from reddiy import reddiy_bot, reddiy_prompts, reddiy_install
    from reddiy.integrations import fi_reddit
    assert True


def test_prompts_structure():
    from reddiy import reddiy_prompts
    assert hasattr(reddiy_prompts, "main_prompt")
    assert len(reddiy_prompts.main_prompt) > 500
    assert "Reddiy" in reddiy_prompts.main_prompt
    assert "Flexus" in reddiy_prompts.main_prompt


def test_install_schema():
    from reddiy import reddiy_install
    schema = reddiy_install.REDDIY_SETUP_SCHEMA
    assert isinstance(schema, list)
    assert len(schema) > 0

    field_names = [field["bs_name"] for field in schema]
    assert "REDDIT_CLIENT_ID" in field_names
    assert "REDDIT_CLIENT_SECRET" in field_names
    assert "REDDIT_USERNAME" in field_names
    assert "REDDIT_REFRESH_TOKEN" in field_names
    assert "TARGET_SUBREDDITS" in field_names
    assert "BRAND_MENTION_STYLE" in field_names
    assert "MAX_POSTS_PER_DAY" in field_names


def test_tools_defined():
    from reddiy import reddiy_bot
    tools = reddiy_bot.TOOLS
    assert len(tools) > 0

    tool_names = [tool.name for tool in tools]
    assert "reddit_monitor" in tool_names
    assert "reddit_reply" in tool_names
    assert "reddit_approve_reply" in tool_names
    assert "reddit_status" in tool_names
    assert "reddit_insights" in tool_names
    assert "reddit_api" in tool_names


def test_keywords_defined():
    from reddiy import reddiy_bot
    keywords = reddiy_bot.RELEVANT_KEYWORDS
    assert isinstance(keywords, list)
    assert len(keywords) > 0
    assert "ai automation" in keywords
    assert "ai agents" in keywords


def test_tool_schemas():
    from reddiy import reddiy_bot

    monitor_tool = reddiy_bot.REDDIT_MONITOR_TOOL
    assert monitor_tool.strict == True
    assert monitor_tool.name == "reddit_monitor"

    reply_tool = reddiy_bot.REDDIT_REPLY_TOOL
    assert reply_tool.strict == True
    assert "submission_id" in reply_tool.parameters["properties"]
    assert "reply_text" in reply_tool.parameters["properties"]
    assert "is_promotional" in reply_tool.parameters["properties"]


def test_reddit_integration_init():
    from reddiy.integrations import fi_reddit

    integration = fi_reddit.IntegrationReddit(
        fclient=None,
        rcx=None,
        client_id="test_id",
        client_secret="test_secret",
        username="test_user",
        refresh_token="",
    )

    assert integration.client_id == "test_id"
    assert integration.client_secret == "test_secret"
    assert integration.username == "test_user"


@pytest.mark.skipif(
    not os.environ.get("REDDIT_CLIENT_ID"),
    reason="REDDIT_CLIENT_ID not set"
)
@pytest.mark.asyncio
async def test_reddit_api_auth():
    """Test Reddit API authentication with real credentials."""
    from reddiy.integrations import fi_reddit

    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    username = os.environ.get("REDDIT_USERNAME", "test_user")
    refresh_token = os.environ.get("REDDIT_REFRESH_TOKEN", "")

    integration = fi_reddit.IntegrationReddit(
        fclient=None,
        rcx=None,
        client_id=client_id,
        client_secret=client_secret,
        username=username,
        refresh_token=refresh_token,
    )

    assert integration.reddit is not None

    if not refresh_token:
        pytest.skip("No refresh token - OAuth flow needed")

    result = integration._test_auth()
    assert "AUTHENTICATED" in result or "ERROR" in result


@pytest.mark.skipif(
    not os.environ.get("REDDIT_REFRESH_TOKEN"),
    reason="REDDIT_REFRESH_TOKEN not set - complete OAuth first"
)
@pytest.mark.asyncio
async def test_reddit_get_subreddit_rules():
    """Test fetching subreddit rules with real API."""
    from reddiy.integrations import fi_reddit

    integration = fi_reddit.IntegrationReddit(
        fclient=None,
        rcx=None,
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        username=os.environ.get("REDDIT_USERNAME", "test"),
        refresh_token=os.environ["REDDIT_REFRESH_TOKEN"],
    )

    result = integration._get_subreddit_rules("startups")
    assert "ERROR" not in result

    data = json.loads(result)
    assert "subreddit" in data
    assert "rules" in data
    assert data["subreddit"] == "startups"


@pytest.mark.skipif(
    not os.environ.get("REDDIT_REFRESH_TOKEN"),
    reason="REDDIT_REFRESH_TOKEN not set - complete OAuth first"
)
def test_reddit_get_new_posts():
    """Test fetching new posts from a subreddit."""
    from reddiy.integrations import fi_reddit

    integration = fi_reddit.IntegrationReddit(
        fclient=None,
        rcx=None,
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        username=os.environ.get("REDDIT_USERNAME", "test"),
        refresh_token=os.environ["REDDIT_REFRESH_TOKEN"],
    )

    posts = integration.get_new_posts("startups", limit=5)
    assert isinstance(posts, list)

    if len(posts) > 0:
        post = posts[0]
        assert "id" in post
        assert "title" in post
        assert "subreddit" in post


@pytest.mark.skipif(
    not os.environ.get("REDDIT_REFRESH_TOKEN"),
    reason="REDDIT_REFRESH_TOKEN not set - complete OAuth first"
)
def test_reddit_account_stats():
    """Test fetching account statistics."""
    from reddiy.integrations import fi_reddit

    integration = fi_reddit.IntegrationReddit(
        fclient=None,
        rcx=None,
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        username=os.environ.get("REDDIT_USERNAME", "test"),
        refresh_token=os.environ["REDDIT_REFRESH_TOKEN"],
    )

    stats = integration.get_account_stats()
    assert "authenticated" in stats

    if stats["authenticated"]:
        assert "username" in stats
        assert "total_karma" in stats
