import time

class GitHubMiner:
    def __init__(self, token=None):
        self.token = token or "demo_token"

    def get_recent_commits(self, username, days=7):
        return [
            {
                "repo": "exus-core",
                "hash": "a1b2c3d",
                "message": "refactor: optimize commitment generator",
                "timestamp": int(time.time()) - 86400,
                "stats": {"total": 150, "additions": 120, "deletions": 30}
            },
            {
                "repo": "exus-chain",
                "hash": "e4f5g6h",
                "message": "fix: patch temporal graph indexing",
                "timestamp": int(time.time()) - 172800,
                "stats": {"total": 45, "additions": 20, "deletions": 25}
            }
        ]

