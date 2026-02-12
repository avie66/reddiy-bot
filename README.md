# Reddiy - Reddit Engagement Bot for Flexus

Reddiy is an autonomous Reddit engagement specialist bot that builds authentic brand awareness for Flexus by monitoring relevant discussions and engaging with value-first responses.

## Purpose

Build Flexus brand awareness on Reddit through:
- Finding relevant discussions about AI automation, business tools, and productivity
- Providing genuine value and solving real problems first
- Mentioning Flexus only when truly relevant and helpful
- Building karma and reputation through authentic engagement
- Maintaining safety through risk detection and approval workflows

## About Flexus

Flexus provides AI teammates that think, act, and take ownership like real specialists:
- Different teammates for different tasks (idea validation, customer acquisition, growth)
- They remember everything, work as a team, learn over time
- Share collective intelligence across the workspace
- Take initiative proactively but keep humans in the loop for important decisions
- More than chatbots - autonomous specialists with tools and long-term memory

## Target Audience

Discussions about:
- AI automation and AI agents
- Business automation and workflow tools
- SaaS products and startup operations
- Productivity tools and team collaboration
- Customer acquisition and growth hacking
- Product validation and market research

## Core Features

### 1. Reddit OAuth Integration

- Secure OAuth2 authentication flow
- Automatic token refresh
- Uses PRAW (Python Reddit API Wrapper) library
- Setup schema includes: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_REFRESH_TOKEN

### 2. Subreddit Monitoring

- Configurable list of target subreddits
- Monitors every 15 minutes via scheduled job
- Tracks new posts and rising posts
- Keyword matching for Flexus-relevant topics
- Stores monitored posts in MongoDB to avoid reprocessing

**Relevant Keywords**: ai automation, ai agents, business automation, workflow automation, productivity tool, saas tool, customer acquisition, growth hack, startup operation, team collaboration, product validation, market research, autonomous agent, ai teammate, ai assistant

### 3. Smart Reply Engine

- Analyzes subreddit rules before posting
- Generates contextual, value-first replies
- Two reply modes:
  - **Safe replies** (auto-post): Helpful information, no links, no brand mention
  - **Promotional replies** (manual approval): Includes Flexus mention or link

### 4. Approval Workflow

Flags for manual approval when:
- Reply includes a link
- Post has >100 upvotes (high visibility)
- Reply includes "Flexus" brand mention
- Daily post limit approaching

Creates kanban task with draft reply for human review. Approved replies post to Reddit and track metrics.

### 5. Risk Detection & Safety

Tracks:
- Comment removal rate (>10% triggers pause)
- Downvote patterns (avg score monitoring)
- Posting frequency (max posts per day/subreddit)
- Subreddit-specific performance

Pauses auto-posting if risk detected and creates alert task.

### 6. Karma Building Strategy

- Suggests "safe engagement" opportunities (no promotion)
- Tracks which subreddits give best results
- Spaces out activity naturally (default: max 20 posts/day)
- Prioritizes value-first engagement

### 7. Analytics & Insights

Tracks:
- Engagement metrics (upvotes, replies, karma)
- Best-performing subreddits
- Posting patterns and effectiveness
- Daily summary reports

## Bot Structure

```
reddiy/
├── __init__.py
├── reddiy_bot.py              # Main bot with scheduled monitoring
├── reddiy_prompts.py          # System prompts for reply generation
├── reddiy_install.py          # Marketplace installation
├── reddiy-1024x1536.webp      # Marketplace image
├── reddiy-256x256.webp        # Avatar
└── integrations/
    ├── __init__.py
    └── fi_reddit.py           # Reddit OAuth integration module
```

## Schedule

**Every 15 minutes**:
- Monitor target subreddits for new opportunities
- Generate and post safe replies automatically
- Create kanban tasks for promotional replies

**Daily**:
- Check account health and risk metrics
- Generate analytics and insights report
- Post summary to kanban

**Every 5 minutes**:
- Check inbox for approval tasks (SCHED_TASK_SORT)
- Work on TODO approval tasks (SCHED_TODO)

## Tools

### reddit_monitor
Check target subreddits for new opportunities.
- Scans new and rising posts
- Matches against relevant keywords
- Returns opportunities with context
- Stores in MongoDB to avoid reprocessing

### reddit_reply
Generate and post reply to a Reddit post.
- `submission_id`: Reddit post ID
- `reply_text`: The reply to post
- `is_promotional`: True if mentions Flexus or includes links
- Safe replies auto-post immediately
- Promotional replies create kanban approval task

### reddit_approve_reply
Approve and post queued reply from kanban task.
- `task_id`: Kanban task ID with the reply
- `approved`: True to post, False to reject
- `edited_reply`: Optional edited version
- Posts to Reddit and tracks metrics

### reddit_status
Check Reddit account health.
- Account karma levels
- Daily post count vs limit
- Recent activity by subreddit
- Removal rate and avg score per subreddit

### reddit_insights
Get analytics and recommendations.
- `days`: Number of days to analyze (default: 7)
- Total posts and breakdown by subreddit
- Promotional vs value-only ratio
- Strategy recommendations

### reddit_api
Direct Reddit API access for OAuth and data retrieval.
- `get_auth_url`: Get OAuth authorization URL
- `exchange_code`: Exchange code for refresh token
- `test_auth`: Test authentication status
- `get_submission`: Fetch post details
- `get_comments`: Fetch post comments
- `get_subreddit_rules`: Check subreddit rules

### Standard Tools
- `mongo_store`: File storage and retrieval
- `flexus_policy_document`: Policy document management
- `ask_questions`: Interactive user questions
- `print_widget`: UI widgets for setup/navigation
- `flexus_bot_kanban`: Kanban board operations

## Setup Schema

### Reddit API (Required)
- **REDDIT_CLIENT_ID**: Reddit application client ID (from https://www.reddit.com/prefs/apps)
- **REDDIT_CLIENT_SECRET**: Reddit application client secret
- **REDDIT_USERNAME**: Reddit account username to post from
- **REDDIT_REFRESH_TOKEN**: OAuth refresh token (obtained via OAuth flow, initially empty)

### Monitoring (Required)
- **TARGET_SUBREDDITS**: Comma-separated list of subreddits (default: "startups,SaaS,Entrepreneur,smallbusiness")

### Engagement (Optional)
- **BRAND_MENTION_STYLE**: How often to mention Flexus: subtle/moderate/direct (default: "moderate")
- **MAX_POSTS_PER_DAY**: Maximum posts per day across all subreddits (default: 20)

## Setup Instructions

### 1. Create Reddit Application

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Choose "script" type
4. Name: "Flexus Reddiy Bot"
5. Description: "Reddit engagement bot for Flexus"
6. Redirect URI: http://localhost:8080
7. Click "Create app"
8. Copy the client ID (under app name) and secret

### 2. Install and Configure Bot

```bash
# Install package
pip install -e /workspace

# Install bot to marketplace
python -m reddiy.reddiy_install --ws=$FLEXUS_WORKSPACE
```

### 3. Complete OAuth Flow

After hiring the bot in Flexus:
1. Talk to Reddiy - it will detect missing credentials
2. Enter REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME in bot settings
3. Use the `reddit_api` tool with `op: "get_auth_url"` to get authorization URL
4. Visit the URL and authorize the app
5. Copy the code from the redirect URL (code parameter)
6. Use `reddit_api` with `op: "exchange_code"` and the code
7. Refresh token is automatically saved to bot settings

### 4. Configure Monitoring

- Set TARGET_SUBREDDITS to communities you want to monitor
- Adjust BRAND_MENTION_STYLE based on your approach
- Set MAX_POSTS_PER_DAY to control activity level

## MongoDB Collections

### monitored_posts
Tracks discovered posts to avoid reprocessing.
```json
{
  "post_id": "abc123",
  "subreddit": "startups",
  "title": "Looking for AI automation tools",
  "discovered_at": 1234567890.0,
  "status": "discovered|replied|pending_approval|rejected",
  "replied_at": 1234567890.0,
  "task_id": "ktask_xyz"
}
```

### activity_log
Records all bot actions for analytics.
```json
{
  "timestamp": 1234567890.0,
  "action": "posted",
  "details": {
    "submission_id": "abc123",
    "subreddit": "startups",
    "reply_length": 250,
    "is_promotional": false
  }
}
```

### risk_metrics
Daily metrics per subreddit for risk monitoring.
```json
{
  "date": "2026-02-12",
  "subreddit": "startups",
  "post_count": 5,
  "total_score": 25,
  "removed_count": 0,
  "last_updated": 1234567890.0
}
```

## Brand Mention Guidelines

### Subtle Style
- Mention Flexus only if directly asked or extremely relevant
- Focus on the category (AI teammates, autonomous agents)
- Let the solution speak for itself

### Moderate Style (Default)
- Mention Flexus when it directly solves stated problem
- Brief description of capabilities
- Always lead with value, product mention secondary

### Direct Style
- More liberal mentions but still value-first
- Include more product details
- Still avoid pure self-promotion

## Safety Rules

**Never auto-post**:
- Replies that violate subreddit rules
- Pure self-promotion without value
- Off-topic or forced mentions
- Anything that could be seen as spam

**Always flag for approval**:
- Replies with external links
- Mentions of "Flexus" brand name
- Posts with >100 upvotes (high visibility)
- Subreddits with strict anti-promotion rules

**Risk Thresholds**:
- Removal rate >10%: Pause and review
- Average score <0: Pause and review
- >5 posts/day per subreddit: Throttle

## Testing

### Import Check
```bash
python -c "from reddiy import reddiy_bot, reddiy_prompts, reddiy_install; print('OK')"
```

### Integration Tests
```bash
pytest tests/ -v
```

Tests require real Reddit API credentials in environment:
- REDDIT_CLIENT_ID
- REDDIT_CLIENT_SECRET
- REDDIT_USERNAME
- REDDIT_REFRESH_TOKEN

### Run Bot
```bash
python -m reddiy.reddiy_bot
```

## Dependencies

- flexus-client-kit: Flexus platform integration
- praw>=7.7.1: Python Reddit API Wrapper
- prawcore>=2.4.0: PRAW core
- motor>=3.3.2: Async MongoDB driver
- pymongo>=4.6.1: MongoDB driver

## Version

0.1.0

## Model

grok-4-1-fast-reasoning (complex planning and analysis)

## License

Proprietary - Flexus
