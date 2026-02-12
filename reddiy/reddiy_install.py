import asyncio
import json
import base64
from pathlib import Path
from flexus_client_kit import ckit_client, ckit_bot_install, ckit_cloudtool
from flexus_client_kit.ckit_bot_install import FMarketplaceExpertInput
from reddiy import reddiy_prompts
from reddiy.integrations import fi_reddit

BOT_NAME = "reddiy"
BOT_VERSION = "0.1.0"

REDDIY_SETUP_SCHEMA = [
    {
        "bs_name": "TARGET_SUBREDDITS",
        "bs_type": "string_long",
        "bs_default": "startups,SaaS,Entrepreneur,smallbusiness",
        "bs_group": "Monitoring",
        "bs_description": "Comma-separated list of subreddits to monitor (without r/)",
        "bs_importance": 0,
    },
    {
        "bs_name": "BRAND_MENTION_STYLE",
        "bs_type": "string_short",
        "bs_default": "moderate",
        "bs_group": "Engagement",
        "bs_description": "How often to mention Flexus: subtle, moderate, or direct",
        "bs_importance": 1,
    },
    {
        "bs_name": "MAX_POSTS_PER_DAY",
        "bs_type": "int",
        "bs_default": 20,
        "bs_group": "Engagement",
        "bs_description": "Maximum posts per day across all subreddits",
        "bs_importance": 1,
    },
] + fi_reddit.REDDIT_SETUP_SCHEMA

async def install(
    client: ckit_client.FlexusClient,
    ws_id: str,
    bot_name: str,
    bot_version: str,
    tools: list[ckit_cloudtool.CloudTool],
):
    bot_internal_tools = json.dumps([t.openai_style_tool() for t in tools])
    pic_big = base64.b64encode(open(Path(__file__).with_name("reddiy-1024x1536.webp"), "rb").read()).decode("ascii")
    pic_small = base64.b64encode(open(Path(__file__).with_name("reddiy-256x256.webp"), "rb").read()).decode("ascii")

    await ckit_bot_install.marketplace_upsert_dev_bot(
        client,
        ws_id=ws_id,
        marketable_name=bot_name,
        marketable_version=bot_version,
        marketable_accent_color="#FF6B35",
        marketable_title1="Reddiy",
        marketable_title2="Reddit engagement specialist for Flexus brand awareness",
        marketable_author="Flexus",
        marketable_occupation="Brand Awareness Specialist",
        marketable_description="Reddiy builds authentic Flexus brand awareness on Reddit through value-first engagement. Monitors target subreddits, generates contextual replies, and maintains safety through approval workflows and risk detection.",
        marketable_typical_group="Marketing",
        marketable_github_repo="",
        marketable_run_this="python -m reddiy.reddiy_bot",
        marketable_setup_default=REDDIY_SETUP_SCHEMA,
        marketable_featured_actions=[
            {"feat_question": "Check Reddit status and recent activity", "feat_expert": "default", "feat_depends_on_setup": ["REDDIT_REFRESH_TOKEN"]},
            {"feat_question": "Monitor subreddits for new opportunities", "feat_expert": "default", "feat_depends_on_setup": ["REDDIT_REFRESH_TOKEN"]},
            {"feat_question": "Show me analytics and insights", "feat_expert": "default", "feat_depends_on_setup": ["REDDIT_REFRESH_TOKEN"]},
        ],
        marketable_intro_message="👋 I'm Reddiy! I help build Flexus brand awareness on Reddit through authentic, value-first engagement. Let me check if you have Reddit API credentials set up...",
        marketable_preferred_model_default="grok-4-1-fast-reasoning",
        marketable_daily_budget_default=100,
        marketable_default_inbox_default=0,
        marketable_picture_big_b64=pic_big,
        marketable_picture_small_b64=pic_small,
        marketable_experts=[
            ("default", FMarketplaceExpertInput(
                fexp_system_prompt=reddiy_prompts.main_prompt,
                fexp_python_kernel="",
                fexp_block_tools="",
                fexp_allow_tools="",
                fexp_app_capture_tools=bot_internal_tools,
                fexp_description="Main expert for Reddit engagement, monitoring, and brand awareness",
            )),
        ],
        marketable_schedule=[
            {
                "sched_type": "SCHED_ANY",
                "sched_when": "EVERY:15m",
                "sched_first_question": "Run reddit_monitor to check for new opportunities, then use reddit_reply for promising posts",
                "sched_fexp_name": "default",
            },
            {
                "sched_type": "SCHED_ANY",
                "sched_when": "EVERY:24h",
                "sched_first_question": "Run reddit_status to check health, then reddit_insights to generate analytics. Post a summary to kanban.",
                "sched_fexp_name": "default",
            },
            {
                "sched_type": "SCHED_TASK_SORT",
                "sched_when": "EVERY:5m",
                "sched_first_question": "Check inbox for approval tasks, prioritize and move to TODO",
                "sched_fexp_name": "default",
            },
            {
                "sched_type": "SCHED_TODO",
                "sched_when": "EVERY:5m",
                "sched_first_question": "Review the reply draft, approve if appropriate, move to done when posted",
                "sched_fexp_name": "default",
            },
        ],
        marketable_tags=["Marketing", "Social Media", "Engagement", "Reddit"],
        marketable_forms=ckit_bot_install.load_form_bundles(__file__),
    )
    print(f"✅ {bot_name} v{bot_version} installed successfully")

if __name__ == "__main__":
    import sys
    if "--ws" in sys.argv:
        fclient = ckit_client.FlexusClient(
            ckit_client.bot_service_name(BOT_NAME, BOT_VERSION),
            endpoint="/v1/jailed-bot",
        )
        from reddiy import reddiy_bot
        asyncio.run(install(fclient, fclient.ws_id, BOT_NAME, BOT_VERSION, reddiy_bot.TOOLS))
    else:
        print("Usage: python -m reddiy.reddiy_install --ws=$FLEXUS_WORKSPACE")
