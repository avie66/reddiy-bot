import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient

from flexus_client_kit import (
    ckit_client,
    ckit_bot_exec,
    ckit_shutdown,
    ckit_cloudtool,
    ckit_mongo,
    ckit_kanban,
)
from flexus_client_kit.integrations import fi_mongo_store, fi_pdoc, fi_question, fi_widget

from reddiy import reddiy_install
from reddiy.integrations import fi_reddit

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_NAME = "reddiy"
BOT_VERSION = "0.1.0"

REDDIT_MONITOR_TOOL = ckit_cloudtool.CloudTool(
    strict=False,
    name="reddit_monitor",
    description="Monitor target subreddits for new engagement opportunities. Returns posts matching Flexus-relevant topics.",
    parameters={
        "type": "object",
        "properties": {
            "limit_per_subreddit": {
                "type": "integer",
                "description": "Max posts to check per subreddit (default: 25)",
            },
        },
        "required": [],
    },
)

REDDIT_REPLY_TOOL = ckit_cloudtool.CloudTool(
    strict=True,
    name="reddit_reply",
    description="Generate and post reply to a Reddit post. Safe replies auto-post, promotional replies create approval task.",
    parameters={
        "type": "object",
        "properties": {
            "submission_id": {
                "type": "string",
                "description": "Reddit post ID to reply to",
            },
            "reply_text": {
                "type": "string",
                "description": "The reply text to post",
            },
            "is_promotional": {
                "type": "boolean",
                "description": "True if reply mentions Flexus or includes links",
            },
        },
        "required": ["submission_id", "reply_text", "is_promotional"],
        "additionalProperties": False,
    },
)

REDDIT_APPROVE_REPLY_TOOL = ckit_cloudtool.CloudTool(
    strict=False,
    name="reddit_approve_reply",
    description="Approve and post a queued promotional reply from kanban task.",
    parameters={
        "type": "object",
        "properties": {
            "task_id": {
                "type": "string",
                "description": "Kanban task ID containing the reply",
            },
            "approved": {
                "type": "boolean",
                "description": "True to post, False to reject",
            },
            "edited_reply": {
                "type": "string",
                "description": "Optional edited reply text",
            },
        },
        "required": ["task_id", "approved"],
    },
)

REDDIT_STATUS_TOOL = ckit_cloudtool.CloudTool(
    strict=False,
    name="reddit_status",
    description="Check Reddit account health, karma, risk metrics, and recent activity.",
    parameters={
        "type": "object",
        "properties": {},
        "required": [],
    },
)

REDDIT_INSIGHTS_TOOL = ckit_cloudtool.CloudTool(
    strict=False,
    name="reddit_insights",
    description="Get analytics: best performing subreddits, trending topics, pain points, and recommendations.",
    parameters={
        "type": "object",
        "properties": {
            "days": {
                "type": "integer",
                "description": "Number of days to analyze (default: 7)",
            },
        },
        "required": [],
    },
)

TOOLS = [
    REDDIT_MONITOR_TOOL,
    REDDIT_REPLY_TOOL,
    REDDIT_APPROVE_REPLY_TOOL,
    REDDIT_STATUS_TOOL,
    REDDIT_INSIGHTS_TOOL,
    fi_reddit.REDDIT_TOOL,
    fi_mongo_store.MONGO_STORE_TOOL,
    fi_pdoc.POLICY_DOCUMENT_TOOL,
    fi_question.ASK_QUESTIONS_TOOL,
    fi_widget.PRINT_WIDGET_TOOL,
]

RELEVANT_KEYWORDS = [
    "ai automation",
    "ai agents",
    "business automation",
    "workflow automation",
    "productivity tool",
    "saas tool",
    "customer acquisition",
    "growth hack",
    "startup operation",
    "team collaboration",
    "product validation",
    "market research",
    "autonomous agent",
    "ai teammate",
    "ai assistant",
]

async def bot_main_loop(fclient: ckit_client.FlexusClient, rcx: ckit_bot_exec.RobotContext):
    setup = ckit_bot_exec.official_setup_mixing_procedure(
        reddiy_install.REDDIY_SETUP_SCHEMA,
        rcx.persona.persona_setup,
    )

    mongo_conn_str = await ckit_mongo.mongo_fetch_creds(fclient, rcx.persona.persona_id)
    mongo = AsyncIOMotorClient(mongo_conn_str, maxPoolSize=50)
    personal_mongo = mongo[rcx.persona.persona_id + "_db"]["personal_mongo"]
    monitored_posts = mongo[rcx.persona.persona_id + "_db"]["monitored_posts"]
    activity_log = mongo[rcx.persona.persona_id + "_db"]["activity_log"]
    risk_metrics = mongo[rcx.persona.persona_id + "_db"]["risk_metrics"]

    await monitored_posts.create_index("post_id", unique=True)
    await activity_log.create_index("timestamp")
    await risk_metrics.create_index("date")

    reddit = fi_reddit.IntegrationReddit(
        fclient,
        rcx,
        client_id=setup.get("REDDIT_CLIENT_ID", ""),
        client_secret=setup.get("REDDIT_CLIENT_SECRET", ""),
        username=setup.get("REDDIT_USERNAME", ""),
        refresh_token=setup.get("REDDIT_REFRESH_TOKEN", ""),
    )

    pdoc = fi_pdoc.IntegrationPdoc(rcx, rcx.persona.ws_root_group_id)

    target_subreddits = [s.strip() for s in setup.get("TARGET_SUBREDDITS", "").split(",") if s.strip()]
    brand_mention_style = setup.get("BRAND_MENTION_STYLE", "moderate")
    max_posts_per_day = setup.get("MAX_POSTS_PER_DAY", 20)

    logger.info(f"Reddiy started: monitoring {target_subreddits}, style={brand_mention_style}, max={max_posts_per_day}/day")

    def is_relevant_post(post: Dict[str, Any]) -> bool:
        text = (post.get("title", "") + " " + post.get("selftext", "")).lower()
        return any(keyword in text for keyword in RELEVANT_KEYWORDS)

    async def get_daily_post_count() -> int:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        count = await activity_log.count_documents({
            "timestamp": {"$gte": today_start},
            "action": "posted",
        })
        return count

    async def log_activity(action: str, details: Dict[str, Any]):
        await activity_log.insert_one({
            "timestamp": time.time(),
            "action": action,
            "details": details,
        })

    async def update_risk_metrics(subreddit: str, score: int, removed: bool):
        today = datetime.utcnow().strftime("%Y-%m-%d")
        await risk_metrics.update_one(
            {"date": today, "subreddit": subreddit},
            {
                "$inc": {
                    "post_count": 1,
                    "total_score": score,
                    "removed_count": 1 if removed else 0,
                },
                "$set": {"last_updated": time.time()},
            },
            upsert=True,
        )

    @rcx.on_tool_call(REDDIT_MONITOR_TOOL.name)
    async def handle_monitor(toolcall, args):
        limit = args.get("limit_per_subreddit", 25)
        opportunities = []

        for subreddit in target_subreddits:
            new_posts = reddit.get_new_posts(subreddit, limit=limit)
            rising_posts = reddit.get_rising_posts(subreddit, limit=limit)
            all_posts = new_posts + rising_posts

            for post in all_posts:
                existing = await monitored_posts.find_one({"post_id": post["id"]})
                if existing:
                    continue

                if is_relevant_post(post):
                    opportunities.append(post)
                    await monitored_posts.insert_one({
                        "post_id": post["id"],
                        "subreddit": post["subreddit"],
                        "title": post["title"],
                        "discovered_at": time.time(),
                        "status": "discovered",
                    })

        if not opportunities:
            return "No new opportunities found."

        result = f"Found {len(opportunities)} opportunities:\n\n"
        for i, post in enumerate(opportunities[:10], 1):
            result += f"{i}. r/{post['subreddit']}: {post['title'][:80]}\n"
            result += f"   ID: {post['id']}, Score: {post['score']}, Comments: {post['num_comments']}\n\n"

        return result

    @rcx.on_tool_call(REDDIT_REPLY_TOOL.name)
    async def handle_reply(toolcall, args):
        submission_id = args["submission_id"]
        reply_text = args["reply_text"]
        is_promotional = args["is_promotional"]

        post_count = await get_daily_post_count()
        if post_count >= max_posts_per_day:
            return f"Daily limit reached ({max_posts_per_day} posts). Reply queued for tomorrow."

        post = await monitored_posts.find_one({"post_id": submission_id})
        if not post:
            return "ERROR: Post not found in monitored collection."

        if is_promotional or post.get("score", 0) > 100:
            task_id = await ckit_kanban.bot_kanban_post_into_inbox(
                fclient,
                rcx.persona.persona_id,
                title=f"Approve reply to r/{post.get('subreddit')}: {post.get('title', '')[:50]}",
                details_json={
                    "submission_id": submission_id,
                    "reply_text": reply_text,
                    "post_title": post.get("title", ""),
                    "subreddit": post.get("subreddit", ""),
                    "post_url": f"https://reddit.com/r/{post.get('subreddit')}/comments/{submission_id}",
                },
                provenance_message="reddit_reply_approval",
            )
            await monitored_posts.update_one(
                {"post_id": submission_id},
                {"$set": {"status": "pending_approval", "task_id": task_id}},
            )
            return f"Reply flagged for approval (promotional or high visibility). Created kanban task: {task_id}"

        result = reddit.reply_to_post(submission_id, reply_text)
        if result["success"]:
            await monitored_posts.update_one(
                {"post_id": submission_id},
                {"$set": {"status": "replied", "replied_at": time.time()}},
            )
            await log_activity("posted", {
                "submission_id": submission_id,
                "subreddit": post.get("subreddit"),
                "reply_length": len(reply_text),
                "is_promotional": is_promotional,
            })
            await update_risk_metrics(post.get("subreddit", ""), 0, False)
            return f"✅ Reply posted successfully: {result['permalink']}"
        else:
            return f"ERROR posting reply: {result['error']}"

    @rcx.on_tool_call(REDDIT_APPROVE_REPLY_TOOL.name)
    async def handle_approve(toolcall, args):
        task_id = args["task_id"]
        approved = args["approved"]
        edited_reply = args.get("edited_reply", "")

        tasks = await ckit_kanban.persona_kanban_list(fclient, rcx.persona.persona_id)
        task = next((t for t in tasks if t.ktask_id == task_id), None)

        if not task:
            return f"ERROR: Task {task_id} not found"

        details = task.ktask_details_json
        submission_id = details.get("submission_id", "")
        reply_text = edited_reply if edited_reply else details.get("reply_text", "")

        if not approved:
            await monitored_posts.update_one(
                {"post_id": submission_id},
                {"$set": {"status": "rejected"}},
            )
            return f"Reply rejected. Task marked as done."

        result = reddit.reply_to_post(submission_id, reply_text)
        if result["success"]:
            await monitored_posts.update_one(
                {"post_id": submission_id},
                {"$set": {"status": "replied", "replied_at": time.time()}},
            )
            await log_activity("posted", {
                "submission_id": submission_id,
                "subreddit": details.get("subreddit"),
                "reply_length": len(reply_text),
                "is_promotional": True,
                "approved": True,
            })
            await update_risk_metrics(details.get("subreddit", ""), 0, False)
            return f"✅ Reply posted successfully: {result['permalink']}\nUse flexus_bot_kanban to mark task as done."
        else:
            return f"ERROR posting reply: {result['error']}"

    @rcx.on_tool_call(REDDIT_STATUS_TOOL.name)
    async def handle_status(toolcall, args):
        account = reddit.get_account_stats()
        post_count = await get_daily_post_count()

        recent_metrics = await risk_metrics.find().sort("date", -1).limit(7).to_list(length=7)

        status = {
            "account": account,
            "daily_posts": f"{post_count}/{max_posts_per_day}",
            "recent_activity": [],
        }

        for metric in recent_metrics:
            removal_rate = metric.get("removed_count", 0) / max(metric.get("post_count", 1), 1)
            avg_score = metric.get("total_score", 0) / max(metric.get("post_count", 1), 1)
            status["recent_activity"].append({
                "date": metric["date"],
                "subreddit": metric["subreddit"],
                "posts": metric.get("post_count", 0),
                "avg_score": round(avg_score, 1),
                "removal_rate": round(removal_rate * 100, 1),
            })

        return json.dumps(status, indent=2)

    @rcx.on_tool_call(REDDIT_INSIGHTS_TOOL.name)
    async def handle_insights(toolcall, args):
        days = args.get("days", 7)
        since = time.time() - (days * 86400)

        activities = await activity_log.find({"timestamp": {"$gte": since}}).to_list(length=1000)

        subreddit_stats = {}
        for activity in activities:
            if activity["action"] == "posted":
                sub = activity["details"].get("subreddit", "unknown")
                if sub not in subreddit_stats:
                    subreddit_stats[sub] = {"posts": 0, "promotional": 0}
                subreddit_stats[sub]["posts"] += 1
                if activity["details"].get("is_promotional"):
                    subreddit_stats[sub]["promotional"] += 1

        insights = {
            "period_days": days,
            "total_posts": len([a for a in activities if a["action"] == "posted"]),
            "subreddit_performance": subreddit_stats,
            "recommendations": [],
        }

        if insights["total_posts"] < 10:
            insights["recommendations"].append("Increase monitoring frequency or add more subreddits")

        for sub, stats in subreddit_stats.items():
            promo_rate = stats["promotional"] / max(stats["posts"], 1)
            if promo_rate > 0.5:
                insights["recommendations"].append(f"r/{sub}: too promotional ({promo_rate:.0%}), add more value-only posts")

        return json.dumps(insights, indent=2)

    @rcx.on_tool_call(fi_reddit.REDDIT_TOOL.name)
    async def handle_reddit_api(toolcall, args):
        return await reddit.called_by_model(toolcall, args)

    @rcx.on_tool_call(fi_mongo_store.MONGO_STORE_TOOL.name)
    async def handle_mongo(toolcall, args):
        return await fi_mongo_store.handle_mongo_store(rcx.workdir, personal_mongo, toolcall, args)

    @rcx.on_tool_call(fi_pdoc.POLICY_DOCUMENT_TOOL.name)
    async def handle_pdoc(toolcall, args):
        return await pdoc.called_by_model(toolcall, args)

    @rcx.on_tool_call(fi_question.ASK_QUESTIONS_TOOL.name)
    async def handle_questions(toolcall, args):
        return fi_question.handle_ask_questions(toolcall, args)

    @rcx.on_tool_call(fi_widget.PRINT_WIDGET_TOOL.name)
    async def handle_widget(toolcall, args):
        return fi_widget.handle_print_widget(toolcall, args)

    try:
        while not ckit_shutdown.shutdown_event.is_set():
            await rcx.unpark_collected_events(sleep_if_no_work=10.0)
    finally:
        await rcx.wait_for_bg_tasks()
        mongo.close()
        logger.info("Reddiy shut down cleanly")

if __name__ == "__main__":
    fclient = ckit_client.FlexusClient(
        ckit_client.bot_service_name(BOT_NAME, BOT_VERSION),
        endpoint="/v1/jailed-bot",
    )

    scenario_fn = ckit_bot_exec.parse_bot_args()

    asyncio.run(ckit_bot_exec.run_bots_in_this_group(
        fclient,
        marketable_name=BOT_NAME,
        marketable_version_str=BOT_VERSION,
        bot_main_loop=bot_main_loop,
        inprocess_tools=TOOLS,
        scenario_fn=scenario_fn,
        install_func=reddiy_install.install,
    ))
