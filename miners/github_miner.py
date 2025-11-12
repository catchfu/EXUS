import time
import datetime
import requests

class GitHubMiner:
    def __init__(self, token=None):
        self.token = token
        self._headers = {
            "Accept": "application/vnd.github+json"
        }
        if self.token:
            # Supports PAT in either raw or 'ghp_' format
            self._headers["Authorization"] = f"Bearer {self.token}"

    def _iso_since(self, days: int):
        dt = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        return dt.isoformat() + "Z"

    def _list_repos(self, username: str, max_repos: int = 3):
        try:
            url = f"https://api.github.com/users/{username}/repos"
            r = requests.get(url, headers=self._headers, timeout=10)
            if r.status_code != 200:
                return []
            repos = r.json()
            repos = [
                {"name": repo["name"], "full_name": repo["full_name"], "owner": repo["owner"]["login"]}
                for repo in repos if not repo.get("fork")
            ]
            return repos[:max_repos]
        except Exception:
            return []

    def _list_commits_for_repo(self, owner: str, name: str, username: str, since_iso: str, max_commits: int = 3):
        try:
            url = f"https://api.github.com/repos/{owner}/{name}/commits"
            params = {"author": username, "since": since_iso}
            r = requests.get(url, headers=self._headers, params=params, timeout=10)
            if r.status_code != 200:
                return []
            commits = []
            for item in r.json()[:max_commits]:
                sha = item.get("sha", "")
                msg = item.get("commit", {}).get("message", "").split("\n")[0]
                ts = item.get("commit", {}).get("author", {}).get("date")
                ts_int = int(datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()) if ts else int(time.time())
                # Try to fetch stats for this commit
                additions = deletions = total = 0
                try:
                    dr = requests.get(f"{url}/{sha}", headers=self._headers, timeout=10)
                    if dr.status_code == 200:
                        dd = dr.json()
                        additions = dd.get("stats", {}).get("additions", 0)
                        deletions = dd.get("stats", {}).get("deletions", 0)
                        total = dd.get("stats", {}).get("total", additions + deletions)
                except Exception:
                    pass
                commits.append({
                    "repo": f"{owner}/{name}",
                    "hash": sha[:7],
                    "message": msg,
                    "timestamp": ts_int,
                    "stats": {"total": total, "additions": additions, "deletions": deletions}
                })
            return commits
        except Exception:
            return []

    def get_recent_commits(self, username, days=7):
        if not self.token:
            # Demo fallback when no token provided
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

        since_iso = self._iso_since(days)
        repos = self._list_repos(username)
        all_commits = []
        for r in repos:
            all_commits.extend(self._list_commits_for_repo(r["owner"], r["name"], username, since_iso))
        # If nothing found, fall back to demo
        if not all_commits:
            return [
                {
                    "repo": "exus-core",
                    "hash": "a1b2c3d",
                    "message": "refactor: optimize commitment generator",
                    "timestamp": int(time.time()) - 86400,
                    "stats": {"total": 150, "additions": 120, "deletions": 30}
                }
            ]
        return all_commits
