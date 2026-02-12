import asyncio
import json
import base64
from pathlib import Path
from flexus_client_kit import ckit_client, ckit_bot_install, ckit_cloudtool
from flexus_client_kit.ckit_bot_install import FMarketplaceExpertInput
from reddiy import reddiy_prompts

BOT_NAME = "reddiy"
BOT_VERSION = "0.2.0"

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
        "bs_name": "BRAND_TONE",
        "bs_type": "string_short",
        "bs_default": "professional",
        "bs_group": "Engagement",
        "bs_description": "Brand tone: casual, professional, or technical",
        "bs_importance": 1,
    },
    {
        "bs_name": "ENGAGEMENT_GOAL",
        "bs_type": "string_short",
        "bs_default": "awareness",
        "bs_group": "Engagement",
        "bs_description": "Primary goal: awareness, leads, or community",
        "bs_importance": 1,
    },
    {
        "bs_name": "WEEKLY_ENGAGEMENT_TARGET",
        "bs_type": "int",
        "bs_default": 10,
        "bs_group": "Engagement",
        "bs_description": "Target number of posts per week",
        "bs_importance": 1,
    },
]

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
        marketable_title2="Manual Reddit Workflow Assistant",
        marketable_author="Flexus",
        marketable_occupation="Reddit Engagement Strategist",
        marketable_description="Reddiy is your Reddit engagement strategist - helping you identify opportunities, draft authentic replies, and track performance without any Reddit API automation. Manual posting workflow maintains authenticity while providing strategic guidance and analytics.",
        marketable_typical_group="Marketing",
        marketable_github_repo="",
        marketable_run_this="python -m reddiy.reddiy_bot",
        marketable_setup_default=REDDIY_SETUP_SCHEMA,
        marketable_featured_actions=[
            {"feat_question": "Analyze r/startups for opportunities", "feat_expert": "default", "feat_depends_on_setup": []},
            {"feat_question": "Suggest relevant subreddits for Flexus", "feat_expert": "default", "feat_depends_on_setup": []},
            {"feat_question": "Show me engagement insights", "feat_expert": "default", "feat_depends_on_setup": []},
        ],
        marketable_intro_message="👋 I'm Reddiy, your Reddit engagement strategist! I help you find opportunities, draft replies, and track performance. You post manually to keep it authentic. Ready to start?",
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
                fexp_description="Manual Reddit workflow assistant - identifies opportunities, drafts replies, tracks performance",
            )),
        ],
        marketable_schedule=[
            {
                "sched_type": "SCHED_ANY",
                "sched_when": "WEEKDAYS:MO:FR/08:00",
                "sched_first_question": "Good morning! Generate a daily opportunity digest: analyze target subreddits and present top 5 opportunities with scores and next steps.",
                "sched_fexp_name": "default",
            },
            {
                "sched_type": "SCHED_TASK_SORT",
                "sched_when": "EVERY:10m",
                "sched_first_question": "Check inbox for user questions or engagement reports, prioritize and move to TODO",
                "sched_fexp_name": "default",
            },
            {
                "sched_type": "SCHED_TODO",
                "sched_when": "EVERY:5m",
                "sched_first_question": "Work on the assigned task, move to done when complete",
                "sched_fexp_name": "default",
            },
        ],
        marketable_tags=["Marketing", "Social Media", "Reddit", "Strategy"],
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
