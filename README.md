# Reddiy - Manual Reddit Workflow Assistant

Reddiy is your Reddit engagement strategist - helping you identify opportunities, draft authentic replies, and track performance through a **manual posting workflow**.

## Purpose

Build Flexus brand awareness on Reddit through strategic, authentic engagement:
- Identify high-value discussion opportunities in target subreddits
- Draft multiple reply options (helpful/moderate/promotional) with risk analysis
- Track performance of manually posted content
- Maintain authenticity through manual posting (no automation)
- Learn what works through analytics and insights

## About Flexus

Flexus provides AI teammates that think, act, and take ownership like real specialists:
- Different teammates for different tasks (idea validation, customer acquisition, growth)
- They remember everything, work as a team, learn over time
- Share collective intelligence across the workspace
- Take initiative proactively but keep humans in the loop
- More than chatbots - autonomous specialists with tools and long-term memory

## Key Philosophy

**No Reddit API Required** - This bot uses web scraping to analyze Reddit content. You post manually to maintain authenticity and avoid automation risks.

**Quality Over Quantity** - Focus on building genuine relationships rather than spamming. Better to post 2 great replies than 10 mediocre ones.

**Strategic Guidance** - Reddiy does the research, analysis, and drafting. You bring the human judgment and authenticity.

## Core Features

### 1. Opportunity Discovery

**analyze_subreddit**: Scan subreddits for engagement opportunities
- Web scrapes recent posts (new and rising)
- Identifies Flexus-relevant discussions
- Scores each opportunity (0-100)
- Returns top threads with context and reasoning

**suggest_subreddits**: Recommend relevant communities
- Searches for subreddits matching your keywords
- Analyzes size, activity level, and relevance
- Provides engagement strategy for each

### 2. Thread Analysis

**analyze_thread**: Deep dive into specific thread
- Fetches full thread content and comments
- Assesses sentiment and key pain points
- Calculates opportunity score
- Identifies competition and risk factors
- Recommends optimal engagement approach

**check_subreddit_rules**: Understand community guidelines
- Scrapes subreddit rules from sidebar
- Identifies self-promotion policies
- Analyzes link posting restrictions
- Recommends safe engagement strategy

### 3. Reply Drafting

**draft_reply**: Generate reply options with reasoning
- Creates 3 versions: helpful, moderate, promotional
- Explains reasoning for each version
- Assesses risk level (low/medium/high)
- Stores drafts for reference

**Three Reply Styles:**
- **Helpful** (Low Risk): Pure value, no brand mention, builds karma
- **Moderate** (Medium Risk): Brief Flexus mention when contextually relevant
- **Promotional** (High Risk): Full product description with link, use sparingly

### 4. Performance Tracking

**log_engagement**: Record what you posted
- User provides thread URL, comment URL, reply text, style
- Stores for historical analysis
- Builds performance dataset

**track_performance**: Update metrics on posted content
- User reports current upvotes and replies
- Tracks growth over time
- Provides performance feedback

**reddit_insights**: Analytics and recommendations
- Aggregates performance across posts
- Identifies best-performing subreddits and styles
- Provides strategic recommendations

### 5. Daily Monitoring

**Scheduled Daily Digest** (Weekdays 8am):
- Analyzes target subreddits automatically
- Presents top 5 opportunities with scores
- Posted to chat for user review

## User Workflow

### Daily Monitoring
1. User: "Check r/startups for opportunities"
2. Reddiy: Analyzes recent posts, presents top 3-5 with opportunity scores
3. User: "Draft a reply for the second one"
4. Reddiy: Provides 2-3 reply options (helpful/moderate/promotional) with reasoning
5. User: Manually posts their chosen version on Reddit
6. User: "I posted it, here's the link: [URL]"
7. Reddiy: Logs it for tracking

### Thread Analysis
1. User: "Analyze this thread: https://reddit.com/r/startups/..."
2. Reddiy: Full breakdown - sentiment, pain points, opportunity score, approach
3. User: "Draft 3 reply options"
4. Reddiy: Generates helpful/moderate/promotional versions with explanations
5. User: Manually posts and reports back

### Subreddit Research
1. User: "Find subreddits interested in AI automation"
2. Reddiy: Web search + analysis, recommends top subreddits with rationale
3. User: "Analyze r/SaaS rules and culture"
4. Reddiy: Fetches rules, analyzes culture, provides engagement strategy

## Bot Structure

```
reddiy/
├── __init__.py
├── reddiy_bot.py              # Main bot with manual workflow tools
├── reddiy_prompts.py          # System prompts for strategic guidance
├── reddiy_install.py          # Marketplace installation
├── reddiy-1024x1536.webp      # Marketplace image
├── reddiy-256x256.webp        # Avatar
└── integrations/
    ├── __init__.py
    └── fi_web.py              # Web scraping integration (no Reddit API)
```

## Tools

### Discovery Tools
- **analyze_subreddit**: Scan subreddit for opportunities
- **suggest_subreddits**: Recommend relevant communities
- **analyze_thread**: Deep analysis of specific thread
- **check_subreddit_rules**: Fetch and analyze subreddit rules

### Drafting Tools
- **draft_reply**: Generate reply options with reasoning
- **web_scrape**: Direct web scraping access (fetch_thread, search_subreddit, get_rules, search_reddit)

### Tracking Tools
- **log_engagement**: Record what user posted manually
- **track_performance**: Update metrics on posted content
- **reddit_insights**: Analytics and recommendations

### Standard Tools
- **mongo_store**: File storage and retrieval
- **flexus_policy_document**: Policy document management
- **ask_questions**: Interactive user questions
- **print_widget**: UI widgets for setup/navigation
- **flexus_bot_kanban**: Kanban board operations

## Setup Schema

### Monitoring (Required)
- **TARGET_SUBREDDITS**: Comma-separated list of subreddits (default: "startups,SaaS,Entrepreneur,smallbusiness")

### Engagement (Optional)
- **BRAND_TONE**: Brand voice: casual, professional, technical (default: "professional")
- **ENGAGEMENT_GOAL**: Primary goal: awareness, leads, community (default: "awareness")
- **WEEKLY_ENGAGEMENT_TARGET**: Target posts per week (default: 10)

## Setup Instructions

### 1. Install Bot

```bash
# Install package
pip install -e /workspace

# Install bot to marketplace
python -m reddiy.reddiy_install --ws=$FLEXUS_WORKSPACE
```

### 2. Configure Bot

After hiring in Flexus:
1. Set TARGET_SUBREDDITS to communities you want to monitor
2. Choose BRAND_TONE (casual/professional/technical)
3. Set ENGAGEMENT_GOAL (awareness/leads/community)
4. Adjust WEEKLY_ENGAGEMENT_TARGET based on capacity

### 3. Start Using

Talk to Reddiy to get started:
- "Check r/startups for opportunities"
- "Suggest subreddits for AI automation"
- "Analyze this thread: [URL]"
- "Draft a reply for this thread"

## MongoDB Collections

### opportunities
Discovered threads with analysis:
```json
{
  "thread_url": "https://reddit.com/...",
  "subreddit": "startups",
  "title": "Looking for AI automation tools",
  "opportunity_score": 85,
  "discovered_at": 1234567890.0,
  "status": "discovered"
}
```

### drafts
Generated reply drafts:
```json
{
  "thread_url": "https://reddit.com/...",
  "style": "moderate",
  "draft_text": "This is what AI teammate platforms solve...",
  "reasoning": "Brief Flexus mention in context",
  "risk": "Medium - includes brand name",
  "created_at": 1234567890.0
}
```

### posted_content
User's manually posted content:
```json
{
  "thread_url": "https://reddit.com/...",
  "comment_url": "https://reddit.com/...",
  "reply_text": "Posted content",
  "style": "helpful",
  "posted_at": 1234567890.0,
  "initial_upvotes": 1,
  "current_upvotes": 15,
  "current_replies": 3
}
```

### performance_metrics
Time-series tracking:
```json
{
  "comment_url": "https://reddit.com/...",
  "upvotes": 15,
  "replies": 3,
  "timestamp": 1234567890.0
}
```

### subreddit_intelligence
Learned patterns per subreddit:
```json
{
  "subreddit": "startups",
  "rules": {...},
  "last_analyzed": 1234567890.0,
  "opportunity_count": 5,
  "total_analyses": 10
}
```

## Reddit Best Practices

### Build Trust First
- Start with helpful replies (no promotion)
- Establish karma and credibility
- Participate authentically
- Become a valued community member

### Know the Rules
- Each subreddit has unique culture
- Check rules before engaging
- Some allow self-promotion, some don't
- Always disclose affiliation

### Timing Matters
- Engage in newer threads (better visibility)
- Respond to questions, not statements
- Join active discussions
- Avoid dead threads

### Authenticity Wins
- Be transparent about working on Flexus
- Focus on solving problems first
- Share genuine insights, not pitches
- Build relationships, not transactions

## Strategy Guide

### When to Use Each Reply Style

**Helpful** (Lowest Risk):
- New subreddits where you're building presence
- Establishing karma and credibility
- Topics where Flexus isn't the best fit
- Building trust before any promotion

**Moderate** (Medium Risk):
- Threads where Flexus is contextually relevant
- User asking about general solutions
- You have established presence in subreddit
- Natural fit for brief mention

**Promotional** (High Risk):
- User explicitly asking for tool recommendations
- Perfect fit - Flexus directly solves stated problem
- You have strong karma in subreddit
- Thread allows self-promotion

### Red Flags (Don't Engage)
- Threads explicitly banning self-promotion
- Low-quality or spam discussions
- Completely unrelated topics
- Hostile sentiment toward AI/automation
- Dead threads (>48 hours old, no activity)

### Green Flags (High Opportunity)
- User asking for specific tool recommendations
- Discussion of pain points Flexus solves
- Technical audience interested in AI agents
- Active thread (<12 hours old, <20 comments)
- No competing product mentions yet

## Schedule

**Daily (Weekdays 8am):**
- Analyze target subreddits
- Present top 5 opportunities
- Post summary to chat

**Task Management:**
- SCHED_TASK_SORT: Every 10 minutes
- SCHED_TODO: Every 5 minutes

## Testing

### Import Check
```bash
python -c "from reddiy import reddiy_bot, reddiy_prompts, reddiy_install; print('OK')"
```

### Unit Tests
```bash
pytest tests/ -v
```

Tests verify:
- Module imports work correctly
- Tools are properly defined
- Prompts are structured correctly
- Setup schema is valid
- Web scraping integration works

### Run Bot
```bash
python -m reddiy.reddiy_bot
```

## Dependencies

- flexus-client-kit: Flexus platform integration
- motor>=3.3.2: Async MongoDB driver
- pymongo>=4.6.1: MongoDB driver

**No Reddit API dependencies** - uses web scraping only

## Why Manual Workflow?

**Maintains Authenticity:**
- Real human posting = more genuine engagement
- Avoids detection as bot/automation
- Builds real relationships

**Reduces Risk:**
- No Reddit API rate limits
- No account suspension risks
- No OAuth complexity

**Better Quality:**
- Human judgment on every post
- Context-aware decisions
- Adapts to thread dynamics

**Strategic Focus:**
- Bot does research and drafting
- Human provides judgment and authenticity
- Best of both worlds

## Version

0.2.0

## Model

grok-4-1-fast-reasoning (strategic analysis and planning)

## License

Proprietary - Flexus
