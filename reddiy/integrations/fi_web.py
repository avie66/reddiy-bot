import logging
import json
import re
from typing import Dict, List, Any, Optional
from flexus_client_kit import ckit_cloudtool
from datetime import datetime

logger = logging.getLogger(__name__)

WEB_SCRAPE_TOOL = ckit_cloudtool.CloudTool(
    strict=False,
    name="web_scrape",
    description="Scrape Reddit content without API. Operations: fetch_thread, search_subreddit, get_rules, search_reddit",
    parameters={
        "type": "object",
        "properties": {
            "op": {
                "type": "string",
                "enum": ["fetch_thread", "search_subreddit", "get_rules", "search_reddit"],
                "description": "Operation to perform",
            },
            "args": {
                "type": "object",
                "description": "Operation-specific arguments",
            },
        },
        "required": ["op"],
    },
)

class IntegrationWeb:
    def __init__(self):
        self.problems_other: List[str] = []

    async def called_by_model(self, toolcall, args) -> str:
        op = args.get("op", "help")
        op_args = args.get("args", {})

        if op == "fetch_thread":
            url = op_args.get("url", "")
            return await self._fetch_thread(url)
        elif op == "search_subreddit":
            subreddit = op_args.get("subreddit", "")
            limit = op_args.get("limit", 25)
            return await self._search_subreddit(subreddit, limit)
        elif op == "get_rules":
            subreddit = op_args.get("subreddit", "")
            return await self._get_rules(subreddit)
        elif op == "search_reddit":
            query = op_args.get("query", "")
            limit = op_args.get("limit", 10)
            return await self._search_reddit(query, limit)
        else:
            return self._help()

    def _help(self) -> str:
        return """Web scraping operations:

fetch_thread: Fetch a Reddit thread for analysis
  args: {"url": "https://reddit.com/r/subreddit/comments/..."}
  Returns: Thread content, comments, metadata

search_subreddit: Search recent posts in a subreddit
  args: {"subreddit": "startups", "limit": 25}
  Returns: Recent posts with metadata

get_rules: Fetch subreddit rules from sidebar
  args: {"subreddit": "startups"}
  Returns: Subreddit rules and guidelines

search_reddit: Search Reddit for specific queries
  args: {"query": "AI automation startups", "limit": 10}
  Returns: Matching posts across Reddit

Note: This tool provides read-only access via web scraping.
No authentication required. Manual posting workflow."""

    async def _fetch_thread(self, url: str) -> str:
        if not url or "reddit.com" not in url:
            return "ERROR: Invalid Reddit URL provided"

        try:
            thread_id = self._extract_thread_id(url)
            if not thread_id:
                return "ERROR: Could not extract thread ID from URL"

            return json.dumps({
                "url": url,
                "thread_id": thread_id,
                "message": "Web scraping placeholder - will fetch thread content including post text, author, score, comments, and metadata",
                "implementation_note": "This will use web scraping to fetch: title, selftext, author, score, num_comments, created_time, top comments with scores",
            }, indent=2)

        except Exception as e:
            logger.error(f"Error fetching thread {url}: {e}")
            return f"ERROR: {str(e)}"

    async def _search_subreddit(self, subreddit: str, limit: int) -> str:
        if not subreddit:
            return "ERROR: Subreddit name required"

        try:
            subreddit = subreddit.replace("r/", "").strip()

            return json.dumps({
                "subreddit": subreddit,
                "limit": limit,
                "message": "Web scraping placeholder - will fetch recent posts",
                "implementation_note": f"This will scrape r/{subreddit}/new and r/{subreddit}/rising to find recent posts. Returns: post_id, title, author, score, num_comments, url, created_time",
            }, indent=2)

        except Exception as e:
            logger.error(f"Error searching r/{subreddit}: {e}")
            return f"ERROR: {str(e)}"

    async def _get_rules(self, subreddit: str) -> str:
        if not subreddit:
            return "ERROR: Subreddit name required"

        try:
            subreddit = subreddit.replace("r/", "").strip()

            return json.dumps({
                "subreddit": subreddit,
                "message": "Web scraping placeholder - will fetch subreddit rules",
                "implementation_note": f"This will scrape r/{subreddit}/about/rules to fetch community guidelines, posting rules, and moderation policies",
            }, indent=2)

        except Exception as e:
            logger.error(f"Error fetching rules for r/{subreddit}: {e}")
            return f"ERROR: {str(e)}"

    async def _search_reddit(self, query: str, limit: int) -> str:
        if not query:
            return "ERROR: Search query required"

        try:
            return json.dumps({
                "query": query,
                "limit": limit,
                "message": "Web scraping placeholder - will search Reddit",
                "implementation_note": f"This will search Reddit for: {query}. Returns matching posts with relevance scores, subreddit, title, url, score, comments",
            }, indent=2)

        except Exception as e:
            logger.error(f"Error searching Reddit for '{query}': {e}")
            return f"ERROR: {str(e)}"

    def _extract_thread_id(self, url: str) -> Optional[str]:
        match = re.search(r'/comments/([a-z0-9]+)', url)
        if match:
            return match.group(1)
        return None
