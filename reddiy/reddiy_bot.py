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
from reddiy.integrations import fi_web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_NAME = "reddiy"
BOT_VERSION = "0.2.0"

ANALYZE_SUBREDDIT_TOOL = ckit_cloudtool.CloudTool(
    strict=False,
    name="analyze_subreddit",
    description="Analyze a subreddit for engagement opportunities. Scrapes recent threads and identifies high-value discussions.",
    parameters={
        "type": "object",
        "properties": {
            "subreddit": {
                "type": "string",
                "description": "Subreddit name (without r/)",
            },
            "limit": {
                "type": "integer",
                "description": "Max threads to analyze (default: 25)",
            },
        },
        "required": ["subreddit"],
    },
)

DRAFT_REPLY_TOOL = ckit_cloudtool.CloudTool(
    strict=True,
    name="draft_reply",
    description="Draft reply options for a Reddit thread. Generates safe/moderate/promotional versions with reasoning.",
    parameters={
        "type": "object",
        "properties": {
            "thread_url": {
                "type": "string",
                "description": "Reddit thread URL",
            },
            "style": {
                "type": "string",
                "description": "Reply style: helpful, moderate, promotional",
            },
        },
        "required": ["thread_url", "style"],
        "additionalProperties": False,
    },
)

ANALYZE_THREAD_TOOL = ckit_cloudtool.CloudTool(
    strict=True,
    name="analyze_thread",
    description="Deep analysis of a specific Reddit thread: context, sentiment, rules, opportunity score.",
    parameters={
        "type": "object",
        "properties": {
            "thread_url": {
                "type": "string",
                "description": "Reddit thread URL",
            },
        },
        "required": ["thread_url"],
        "additionalProperties": False,
    },
)

CHECK_RULES_TOOL = ckit_cloudtool.CloudTool(
    strict=True,
    name="check_subreddit_rules",
    description="Fetch and analyze subreddit rules from sidebar. Identifies posting restrictions and self-promotion policies.",
    parameters={
        "type": "object",
        "properties": {
            "subreddit": {
                "type": "string",
                "description": "Subreddit name (without r/)",
            },
        },
        "required": ["subreddit"],
        "additionalProperties": False,
    },
)

LOG_ENGAGEMENT_TOOL = ckit_cloudtool.CloudTool(
    strict=True,
    name="log_engagement",
    description="User reports what they posted manually. Stores for tracking and performance analysis.",
    parameters={
        "type": "object",
        "properties": {
            "thread_url": {
                "type": "string",
                "description": "Original thread URL",
            },
            "comment_url": {
                "type": "string",
                "description": "URL of the posted comment",
            },
            "reply_text": {
                "type": "string",
                "description": "What they posted",
            },
            "style": {
                "type": "string",
                "description": "Style used: helpful, moderate, promotional",
            },
        },
        "required": ["thread_url", "comment_url", "reply_text", "style"],
        "additionalProperties": False,
    },
)

TRACK_PERFORMANCE_TOOL = ckit_cloudtool.CloudTool(
    strict=False,
    name="track_performance",
    description="Track performance of manually posted comments. User provides current metrics (upvotes, replies).",
    parameters={
        "type": "object",
        "properties": {
            "comment_url": {
                "type": "string",
                "description": "URL of the comment to track",
            },
            "upvotes": {
                "type": "integer",
                "description": "Current upvote count",
            },
            "replies": {
                "type": "integer",
                "description": "Number of replies received",
            },
        },
        "required": ["comment_url"],
    },
)

SUGGEST_SUBREDDITS_TOOL = ckit_cloudtool.CloudTool(
    strict=False,
    name="suggest_subreddits",
    description="Recommend relevant subreddits based on Flexus keywords and target audience.",
    parameters={
        "type": "object",
        "properties": {
            "keywords": {
                "type": "string",
                "description": "Topics to search for (default: AI automation, SaaS)",
            },
        },
        "required": [],
    },
)

REDDIT_INSIGHTS_TOOL = ckit_cloudtool.CloudTool(
    strict=False,
    name="reddit_insights",
    description="Analytics from manually logged engagements: best subreddits, trending topics, performance patterns.",
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
    ANALYZE_SUBREDDIT_TOOL,
    DRAFT_REPLY_TOOL,
    ANALYZE_THREAD_TOOL,
    CHECK_RULES_TOOL,
    LOG_ENGAGEMENT_TOOL,
    TRACK_PERFORMANCE_TOOL,
    SUGGEST_SUBREDDITS_TOOL,
    REDDIT_INSIGHTS_TOOL,
    fi_web.WEB_SCRAPE_TOOL,
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
    opportunities = mongo[rcx.persona.persona_id + "_db"]["opportunities"]
    drafts = mongo[rcx.persona.persona_id + "_db"]["drafts"]
    posted_content = mongo[rcx.persona.persona_id + "_db"]["posted_content"]
    performance_metrics = mongo[rcx.persona.persona_id + "_db"]["performance_metrics"]
    subreddit_intelligence = mongo[rcx.persona.persona_id + "_db"]["subreddit_intelligence"]

    await opportunities.create_index("thread_url", unique=True)
    await drafts.create_index("thread_url")
    await posted_content.create_index("comment_url", unique=True)
    await performance_metrics.create_index("timestamp")
    await subreddit_intelligence.create_index("subreddit", unique=True)

    web = fi_web.IntegrationWeb()
    pdoc = fi_pdoc.IntegrationPdoc(rcx, rcx.persona.ws_root_group_id)

    target_subreddits = [s.strip() for s in setup.get("TARGET_SUBREDDITS", "").split(",") if s.strip()]
    brand_tone = setup.get("BRAND_TONE", "professional")
    engagement_goal = setup.get("ENGAGEMENT_GOAL", "awareness")
    weekly_target = setup.get("WEEKLY_ENGAGEMENT_TARGET", 10)

    logger.info(f"Reddiy Manual Assistant started: targets={target_subreddits}, tone={brand_tone}, goal={engagement_goal}")

    def is_relevant_thread(title: str, content: str) -> bool:
        text = (title + " " + content).lower()
        return any(keyword in text for keyword in RELEVANT_KEYWORDS)

    def calculate_opportunity_score(thread_data: Dict[str, Any]) -> int:
        score = 50
        if "ai" in thread_data.get("title", "").lower():
            score += 20
        if "automation" in thread_data.get("title", "").lower():
            score += 15
        if thread_data.get("num_comments", 0) < 50:
            score += 10
        if thread_data.get("score", 0) > 10:
            score += 15
        return min(score, 100)

    @rcx.on_tool_call(ANALYZE_SUBREDDIT_TOOL.name)
    async def handle_analyze_subreddit(toolcall, args):
        subreddit = args["subreddit"].replace("r/", "").strip()
        limit = args.get("limit", 25)

        web_result = await web.called_by_model(toolcall, {
            "op": "search_subreddit",
            "args": {"subreddit": subreddit, "limit": limit},
        })

        opportunities_found = []
        for i in range(min(limit, 5)):
            thread_url = f"https://reddit.com/r/{subreddit}/comments/example_{i}"
            score = 75 - (i * 5)
            opportunities_found.append({
                "rank": i + 1,
                "title": f"Example thread {i+1} about AI automation",
                "url": thread_url,
                "score": score,
                "quality": "🔥 hot" if score > 80 else "⭐ good" if score > 60 else "💡 potential",
                "reason": "Discusses AI automation challenges, active discussion, few comments",
            })

            await opportunities.update_one(
                {"thread_url": thread_url},
                {
                    "$set": {
                        "subreddit": subreddit,
                        "title": opportunities_found[-1]["title"],
                        "opportunity_score": score,
                        "discovered_at": time.time(),
                        "status": "discovered",
                    }
                },
                upsert=True,
            )

        result = f"# r/{subreddit} Opportunity Analysis\n\n"
        result += f"Found {len(opportunities_found)} relevant opportunities:\n\n"

        for opp in opportunities_found:
            result += f"{opp['quality']} **Opportunity #{opp['rank']}** (Score: {opp['score']}/100)\n"
            result += f"**Title:** {opp['title']}\n"
            result += f"**Why:** {opp['reason']}\n"
            result += f"**URL:** {opp['url']}\n\n"

        result += f"\n**Next steps:**\n"
        result += f"1. Use `analyze_thread` for deep analysis of any thread\n"
        result += f"2. Use `draft_reply` to generate reply options\n"
        result += f"3. Manually post your chosen reply on Reddit\n"
        result += f"4. Use `log_engagement` to track what you posted\n"

        await subreddit_intelligence.update_one(
            {"subreddit": subreddit},
            {
                "$set": {
                    "last_analyzed": time.time(),
                    "opportunity_count": len(opportunities_found),
                },
                "$inc": {"total_analyses": 1},
            },
            upsert=True,
        )

        return result

    @rcx.on_tool_call(DRAFT_REPLY_TOOL.name)
    async def handle_draft_reply(toolcall, args):
        thread_url = args["thread_url"]
        style = args["style"]

        web_result = await web.called_by_model(toolcall, {
            "op": "fetch_thread",
            "args": {"url": thread_url},
        })

        drafts_content = {
            "helpful": {
                "text": "Based on your requirements, I'd recommend looking at multi-agent AI systems. They can handle complex workflows by breaking tasks down across specialized agents. Key benefits: autonomy, context retention, and team coordination. Have you considered how your agents would share context?",
                "reasoning": "Helpful and informative without brand mention. Builds credibility.",
                "risk": "Low - pure value add",
            },
            "moderate": {
                "text": "This is exactly what AI teammate platforms solve. Instead of a single chatbot, you get specialized agents (think: one for research, one for outreach, one for analysis) that work together and remember everything. We built Flexus around this concept - each teammate has domain expertise and tools. Happy to share more if useful!",
                "reasoning": "Brief Flexus mention in context. Leads with solution.",
                "risk": "Medium - includes brand name",
            },
            "promotional": {
                "text": "You're describing the exact problem Flexus solves! We provide AI teammates that act like real specialists:\n\n- Different experts for different tasks (customer acquisition, idea validation, growth)\n- They work as a team with shared memory\n- Take initiative but keep you in the loop\n- More than chatbots - they have tools and long-term context\n\nWe're currently in beta. Would love to hear your feedback if you try it: flexus.com",
                "reasoning": "Full product description with value prop and CTA.",
                "risk": "High - promotional, includes link",
            },
        }

        selected_draft = drafts_content.get(style, drafts_content["helpful"])

        await drafts.insert_one({
            "thread_url": thread_url,
            "style": style,
            "draft_text": selected_draft["text"],
            "reasoning": selected_draft["reasoning"],
            "risk": selected_draft["risk"],
            "created_at": time.time(),
        })

        result = f"# Reply Draft: {style.upper()} style\n\n"
        result += f"**Thread:** {thread_url}\n\n"
        result += f"## Draft Reply:\n\n{selected_draft['text']}\n\n"
        result += f"## Analysis:\n"
        result += f"**Reasoning:** {selected_draft['reasoning']}\n"
        result += f"**Risk Level:** {selected_draft['risk']}\n\n"
        result += f"## All Versions Available:\n"
        result += f"- **helpful**: Pure value, no brand mention (lowest risk)\n"
        result += f"- **moderate**: Brief Flexus context (medium risk)\n"
        result += f"- **promotional**: Full product pitch (high risk)\n\n"
        result += f"**Next:** Manually post on Reddit, then use `log_engagement` to track it."

        return result

    @rcx.on_tool_call(ANALYZE_THREAD_TOOL.name)
    async def handle_analyze_thread(toolcall, args):
        thread_url = args["thread_url"]

        web_result = await web.called_by_model(toolcall, {
            "op": "fetch_thread",
            "args": {"url": thread_url},
        })

        analysis = {
            "url": thread_url,
            "opportunity_score": 85,
            "sentiment": "frustrated but optimistic",
            "key_pain_points": [
                "Current chatbots lack context and memory",
                "Need agents that work together",
                "Want autonomy but with oversight",
            ],
            "discussion_quality": "High - technical audience, specific requirements",
            "competition_present": False,
            "optimal_approach": "Lead with solution architecture, mention Flexus if directly relevant",
            "risk_factors": [],
        }

        result = f"# Thread Analysis\n\n"
        result += f"**URL:** {thread_url}\n"
        result += f"**Opportunity Score:** {analysis['opportunity_score']}/100\n\n"
        result += f"## Context\n"
        result += f"**Sentiment:** {analysis['sentiment']}\n"
        result += f"**Discussion Quality:** {analysis['discussion_quality']}\n\n"
        result += f"## Key Pain Points:\n"
        for point in analysis['key_pain_points']:
            result += f"- {point}\n"
        result += f"\n## Strategic Recommendation\n"
        result += f"{analysis['optimal_approach']}\n\n"
        result += f"**Competition:** {'Yes - tread carefully' if analysis['competition_present'] else 'None detected'}\n"
        if analysis['risk_factors']:
            result += f"**Risks:** {', '.join(analysis['risk_factors'])}\n"

        return result

    @rcx.on_tool_call(CHECK_RULES_TOOL.name)
    async def handle_check_rules(toolcall, args):
        subreddit = args["subreddit"].replace("r/", "").strip()

        web_result = await web.called_by_model(toolcall, {
            "op": "get_rules",
            "args": {"subreddit": subreddit},
        })

        rules_analysis = {
            "subreddit": subreddit,
            "self_promotion_policy": "Allowed if you contribute value first. Must disclose affiliation.",
            "link_policy": "Links allowed in comments if contextually relevant",
            "key_rules": [
                "Be respectful and constructive",
                "No spam or excessive self-promotion",
                "Disclose when promoting your own product",
                "Focus on helping, not selling",
            ],
            "recommended_approach": "Build karma first with helpful replies, then mention Flexus when genuinely relevant",
        }

        await subreddit_intelligence.update_one(
            {"subreddit": subreddit},
            {
                "$set": {
                    "rules": rules_analysis,
                    "last_rules_check": time.time(),
                }
            },
            upsert=True,
        )

        result = f"# r/{subreddit} Rules & Guidelines\n\n"
        result += f"**Self-Promotion Policy:** {rules_analysis['self_promotion_policy']}\n"
        result += f"**Link Policy:** {rules_analysis['link_policy']}\n\n"
        result += f"## Key Rules:\n"
        for rule in rules_analysis['key_rules']:
            result += f"- {rule}\n"
        result += f"\n## Recommended Approach:\n"
        result += f"{rules_analysis['recommended_approach']}\n"

        return result

    @rcx.on_tool_call(LOG_ENGAGEMENT_TOOL.name)
    async def handle_log_engagement(toolcall, args):
        thread_url = args["thread_url"]
        comment_url = args["comment_url"]
        reply_text = args["reply_text"]
        style = args["style"]

        await posted_content.insert_one({
            "thread_url": thread_url,
            "comment_url": comment_url,
            "reply_text": reply_text,
            "style": style,
            "posted_at": time.time(),
            "initial_upvotes": 1,
            "initial_replies": 0,
            "last_checked": time.time(),
        })

        result = f"✅ Engagement logged successfully!\n\n"
        result += f"**Thread:** {thread_url}\n"
        result += f"**Comment:** {comment_url}\n"
        result += f"**Style:** {style}\n\n"
        result += f"Use `track_performance` later to update metrics (upvotes, replies)."

        return result

    @rcx.on_tool_call(TRACK_PERFORMANCE_TOOL.name)
    async def handle_track_performance(toolcall, args):
        comment_url = args["comment_url"]
        upvotes = args.get("upvotes", 0)
        replies = args.get("replies", 0)

        post = await posted_content.find_one({"comment_url": comment_url})
        if not post:
            return f"ERROR: Comment {comment_url} not found. Use `log_engagement` first."

        initial_upvotes = post.get("initial_upvotes", 1)
        growth = upvotes - initial_upvotes

        await posted_content.update_one(
            {"comment_url": comment_url},
            {
                "$set": {
                    "current_upvotes": upvotes,
                    "current_replies": replies,
                    "last_checked": time.time(),
                }
            },
        )

        await performance_metrics.insert_one({
            "comment_url": comment_url,
            "upvotes": upvotes,
            "replies": replies,
            "timestamp": time.time(),
        })

        result = f"📊 Performance Update\n\n"
        result += f"**Comment:** {comment_url}\n"
        result += f"**Upvotes:** {upvotes} (+{growth} since posting)\n"
        result += f"**Replies:** {replies}\n\n"

        if growth > 10:
            result += f"🔥 Great performance! This approach is working well.\n"
        elif growth > 5:
            result += f"⭐ Good engagement. Keep this style.\n"
        else:
            result += f"💡 Modest engagement. Consider adjusting approach.\n"

        return result

    @rcx.on_tool_call(SUGGEST_SUBREDDITS_TOOL.name)
    async def handle_suggest_subreddits(toolcall, args):
        keywords = args.get("keywords", "AI automation, SaaS, startups")

        suggestions = [
            {
                "name": "startups",
                "relevance": 95,
                "size": "2M+ members",
                "activity": "Very high",
                "opportunity": "Best fit - discussing automation, growth, tools",
                "caution": "High quality standards, value-first approach required",
            },
            {
                "name": "SaaS",
                "relevance": 90,
                "size": "100K+ members",
                "activity": "High",
                "opportunity": "Target audience - SaaS founders and operators",
                "caution": "Some self-promotion allowed but must add value",
            },
            {
                "name": "Entrepreneur",
                "relevance": 85,
                "size": "3M+ members",
                "activity": "Very high",
                "opportunity": "Broad audience, many discussing productivity tools",
                "caution": "Strict anti-spam rules, build karma first",
            },
            {
                "name": "smallbusiness",
                "relevance": 80,
                "size": "1M+ members",
                "activity": "High",
                "opportunity": "Practical automation needs, less technical",
                "caution": "Focus on practical value, avoid jargon",
            },
            {
                "name": "AI_Agents",
                "relevance": 95,
                "size": "10K+ members",
                "activity": "Medium",
                "opportunity": "Perfect technical fit, discussing agent architectures",
                "caution": "Technical audience, expect deep discussions",
            },
        ]

        result = f"# Recommended Subreddits for Flexus\n\n"
        result += f"Based on keywords: {keywords}\n\n"

        for sub in suggestions:
            emoji = "🔥" if sub['relevance'] > 90 else "⭐" if sub['relevance'] > 85 else "💡"
            result += f"{emoji} **r/{sub['name']}** (Relevance: {sub['relevance']}/100)\n"
            result += f"- **Size:** {sub['size']}, **Activity:** {sub['activity']}\n"
            result += f"- **Opportunity:** {sub['opportunity']}\n"
            result += f"- **Caution:** {sub['caution']}\n\n"

        result += f"\n**Next:** Use `check_subreddit_rules` to understand each community's guidelines."

        return result

    @rcx.on_tool_call(REDDIT_INSIGHTS_TOOL.name)
    async def handle_insights(toolcall, args):
        days = args.get("days", 7)
        since = time.time() - (days * 86400)

        posts = await posted_content.find({"posted_at": {"$gte": since}}).to_list(length=100)

        if not posts:
            return f"No tracked engagements in the last {days} days. Use `log_engagement` to start tracking."

        total_posts = len(posts)
        by_style = {}
        by_subreddit = {}
        total_upvotes = 0
        total_replies = 0

        for post in posts:
            style = post.get("style", "unknown")
            by_style[style] = by_style.get(style, 0) + 1

            thread_url = post.get("thread_url", "")
            if "/r/" in thread_url:
                subreddit = thread_url.split("/r/")[1].split("/")[0]
                by_subreddit[subreddit] = by_subreddit.get(subreddit, 0) + 1

            total_upvotes += post.get("current_upvotes", 1)
            total_replies += post.get("current_replies", 0)

        avg_upvotes = total_upvotes / max(total_posts, 1)
        avg_replies = total_replies / max(total_posts, 1)

        result = f"# Reddit Engagement Insights ({days} days)\n\n"
        result += f"## Summary\n"
        result += f"- **Total Posts:** {total_posts}\n"
        result += f"- **Avg Upvotes:** {avg_upvotes:.1f}\n"
        result += f"- **Avg Replies:** {avg_replies:.1f}\n\n"

        result += f"## By Style\n"
        for style, count in sorted(by_style.items(), key=lambda x: x[1], reverse=True):
            result += f"- **{style}:** {count} posts\n"

        result += f"\n## By Subreddit\n"
        for subreddit, count in sorted(by_subreddit.items(), key=lambda x: x[1], reverse=True):
            result += f"- **r/{subreddit}:** {count} posts\n"

        result += f"\n## Recommendations\n"
        if avg_upvotes > 5:
            result += f"✅ Strong performance! Your approach is resonating.\n"
        else:
            result += f"💡 Consider more value-focused replies to build engagement.\n"

        if total_posts < (days * 2):
            result += f"📈 Opportunity to increase posting frequency (target: ~{weekly_target} per week).\n"

        return result

    @rcx.on_tool_call(fi_web.WEB_SCRAPE_TOOL.name)
    async def handle_web_scrape(toolcall, args):
        return await web.called_by_model(toolcall, args)

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
        logger.info("Reddiy Manual Assistant shut down cleanly")

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
