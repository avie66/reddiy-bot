import logging
import praw
import prawcore
from typing import Optional, Dict, List, Any
from flexus_client_kit import ckit_cloudtool, ckit_bot_exec
import time
import json

logger = logging.getLogger(__name__)

REDDIT_SETUP_SCHEMA = [
    {
        "bs_name": "REDDIT_CLIENT_ID",
        "bs_type": "string_long",
        "bs_default": "",
        "bs_group": "Reddit API",
        "bs_description": "Reddit application client ID (from https://www.reddit.com/prefs/apps)",
        "bs_importance": 0,
    },
    {
        "bs_name": "REDDIT_CLIENT_SECRET",
        "bs_type": "string_long",
        "bs_default": "",
        "bs_group": "Reddit API",
        "bs_description": "Reddit application client secret",
        "bs_importance": 0,
    },
    {
        "bs_name": "REDDIT_USERNAME",
        "bs_type": "string_short",
        "bs_default": "",
        "bs_group": "Reddit API",
        "bs_description": "Reddit account username to post from",
        "bs_importance": 0,
    },
    {
        "bs_name": "REDDIT_REFRESH_TOKEN",
        "bs_type": "string_long",
        "bs_default": "",
        "bs_group": "Reddit API",
        "bs_description": "OAuth refresh token (leave empty, will be obtained via OAuth flow)",
        "bs_importance": 1,
    },
]

REDDIT_TOOL = ckit_cloudtool.CloudTool(
    strict=False,
    name="reddit_api",
    description="Interact with Reddit API. Operations: get_auth_url, exchange_code, test_auth, get_submission, get_comments, get_subreddit_rules",
    parameters={
        "type": "object",
        "properties": {
            "op": {
                "type": "string",
                "enum": ["get_auth_url", "exchange_code", "test_auth", "get_submission", "get_comments", "get_subreddit_rules"],
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

class IntegrationReddit:
    def __init__(self, fclient, rcx, client_id: str, client_secret: str, username: str, refresh_token: str = ""):
        self.fclient = fclient
        self.rcx = rcx
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.refresh_token = refresh_token
        self.reddit: Optional[praw.Reddit] = None
        self.problems_other: List[str] = []
        self._init_reddit()

    def _init_reddit(self):
        if not self.client_id or not self.client_secret:
            self.problems_other.append("Missing client_id or client_secret")
            return

        try:
            if self.refresh_token:
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    refresh_token=self.refresh_token,
                    user_agent=f"Flexus-Reddiy-Bot/0.1 by {self.username}",
                )
                me = self.reddit.user.me()
                logger.info(f"Reddit authenticated as: {me.name}")
            else:
                self.reddit = praw.Reddit(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    user_agent=f"Flexus-Reddiy-Bot/0.1 by {self.username}",
                )
                self.problems_other.append("No refresh_token - need to complete OAuth flow")
        except Exception as e:
            logger.error(f"Reddit init error: {e}")
            self.problems_other.append(f"Init error: {str(e)}")

    async def called_by_model(self, toolcall, args) -> str:
        op = args.get("op", "help")
        op_args = args.get("args", {})

        if op == "get_auth_url":
            return self._get_auth_url()
        elif op == "exchange_code":
            code = op_args.get("code", "")
            return await self._exchange_code(code)
        elif op == "test_auth":
            return self._test_auth()
        elif op == "get_submission":
            submission_id = op_args.get("submission_id", "")
            return self._get_submission(submission_id)
        elif op == "get_comments":
            submission_id = op_args.get("submission_id", "")
            limit = op_args.get("limit", 10)
            return self._get_comments(submission_id, limit)
        elif op == "get_subreddit_rules":
            subreddit = op_args.get("subreddit", "")
            return self._get_subreddit_rules(subreddit)
        else:
            return f"Unknown operation: {op}"

    def _get_auth_url(self) -> str:
        if not self.reddit:
            return "ERROR: Reddit not initialized. Check client_id and client_secret."

        try:
            scopes = ["identity", "read", "submit", "edit", "history"]
            auth_url = self.reddit.auth.url(scopes, "flexus_reddiy_state", "permanent")
            return f"Please authorize the bot by visiting this URL:\n{auth_url}\n\nAfter authorization, you'll receive a code. Use the 'exchange_code' operation with that code."
        except Exception as e:
            return f"ERROR generating auth URL: {str(e)}"

    async def _exchange_code(self, code: str) -> str:
        if not self.reddit:
            return "ERROR: Reddit not initialized."

        try:
            refresh_token = self.reddit.auth.authorize(code)
            from flexus_client_kit import ckit_bot_query
            await ckit_bot_query.persona_setup_patch(
                self.fclient,
                self.rcx.persona.persona_id,
                {"REDDIT_REFRESH_TOKEN": refresh_token},
            )
            self.refresh_token = refresh_token
            self._init_reddit()
            return f"SUCCESS: Refresh token obtained and saved. Bot is now authenticated as u/{self.username}."
        except Exception as e:
            return f"ERROR exchanging code: {str(e)}"

    def _test_auth(self) -> str:
        if not self.reddit or not self.refresh_token:
            return f"NOT_AUTHENTICATED: {', '.join(self.problems_other)}"

        try:
            me = self.reddit.user.me()
            karma = me.link_karma + me.comment_karma
            return f"AUTHENTICATED: u/{me.name}, karma: {karma}, problems: {self.problems_other or 'none'}"
        except Exception as e:
            return f"ERROR testing auth: {str(e)}"

    def _get_submission(self, submission_id: str) -> str:
        if not self.reddit or not self.refresh_token:
            return "ERROR: Not authenticated"

        try:
            submission = self.reddit.submission(id=submission_id)
            data = {
                "id": submission.id,
                "title": submission.title,
                "selftext": submission.selftext[:500],
                "subreddit": str(submission.subreddit),
                "author": str(submission.author),
                "score": submission.score,
                "url": submission.url,
                "num_comments": submission.num_comments,
                "created_utc": submission.created_utc,
            }
            return json.dumps(data, indent=2)
        except Exception as e:
            return f"ERROR fetching submission: {str(e)}"

    def _get_comments(self, submission_id: str, limit: int) -> str:
        if not self.reddit or not self.refresh_token:
            return "ERROR: Not authenticated"

        try:
            submission = self.reddit.submission(id=submission_id)
            submission.comments.replace_more(limit=0)
            comments = []
            for comment in submission.comments.list()[:limit]:
                comments.append({
                    "id": comment.id,
                    "author": str(comment.author),
                    "body": comment.body[:200],
                    "score": comment.score,
                })
            return json.dumps(comments, indent=2)
        except Exception as e:
            return f"ERROR fetching comments: {str(e)}"

    def _get_subreddit_rules(self, subreddit: str) -> str:
        if not self.reddit or not self.refresh_token:
            return "ERROR: Not authenticated"

        try:
            sub = self.reddit.subreddit(subreddit)
            rules = []
            for rule in sub.rules:
                rules.append({
                    "short_name": rule.short_name,
                    "description": rule.description[:300],
                    "kind": rule.kind,
                })
            return json.dumps({"subreddit": subreddit, "rules": rules}, indent=2)
        except Exception as e:
            return f"ERROR fetching rules: {str(e)}"

    def get_new_posts(self, subreddit: str, limit: int = 25) -> List[Dict[str, Any]]:
        if not self.reddit or not self.refresh_token:
            return []

        try:
            sub = self.reddit.subreddit(subreddit)
            posts = []
            for submission in sub.new(limit=limit):
                posts.append({
                    "id": submission.id,
                    "title": submission.title,
                    "selftext": submission.selftext,
                    "subreddit": str(submission.subreddit),
                    "author": str(submission.author),
                    "score": submission.score,
                    "url": submission.url,
                    "num_comments": submission.num_comments,
                    "created_utc": submission.created_utc,
                })
            return posts
        except Exception as e:
            logger.error(f"Error fetching posts from r/{subreddit}: {e}")
            return []

    def get_rising_posts(self, subreddit: str, limit: int = 25) -> List[Dict[str, Any]]:
        if not self.reddit or not self.refresh_token:
            return []

        try:
            sub = self.reddit.subreddit(subreddit)
            posts = []
            for submission in sub.rising(limit=limit):
                posts.append({
                    "id": submission.id,
                    "title": submission.title,
                    "selftext": submission.selftext,
                    "subreddit": str(submission.subreddit),
                    "author": str(submission.author),
                    "score": submission.score,
                    "url": submission.url,
                    "num_comments": submission.num_comments,
                    "created_utc": submission.created_utc,
                })
            return posts
        except Exception as e:
            logger.error(f"Error fetching rising posts from r/{subreddit}: {e}")
            return []

    def reply_to_post(self, submission_id: str, reply_text: str) -> Dict[str, Any]:
        if not self.reddit or not self.refresh_token:
            return {"success": False, "error": "Not authenticated"}

        try:
            submission = self.reddit.submission(id=submission_id)
            comment = submission.reply(reply_text)
            return {
                "success": True,
                "comment_id": comment.id,
                "permalink": f"https://reddit.com{comment.permalink}",
            }
        except Exception as e:
            logger.error(f"Error replying to post {submission_id}: {e}")
            return {"success": False, "error": str(e)}

    def get_account_stats(self) -> Dict[str, Any]:
        if not self.reddit or not self.refresh_token:
            return {"authenticated": False}

        try:
            me = self.reddit.user.me()
            return {
                "authenticated": True,
                "username": me.name,
                "link_karma": me.link_karma,
                "comment_karma": me.comment_karma,
                "total_karma": me.link_karma + me.comment_karma,
                "created_utc": me.created_utc,
            }
        except Exception as e:
            return {"authenticated": False, "error": str(e)}
