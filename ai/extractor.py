import time

class CognitiveExtractor:
    def __init__(self):
        self.weights = {
            "commit_message_sentiment": 0.3,
            "code_complexity_delta": 0.25,
            "refactoring_frequency": 0.2,
            "documentation_ratio": 0.15,
            "review_response_time": 0.1
        }

    def analyze_commit(self, commit):
        msg = commit.get("message", "")
        pos = ["fix", "improve", "optimize", "refactor", "enhance"]
        neg = ["hack", "temporary", "bug", "workaround", "broken"]
        sentiment = sum(1 for w in pos if w in msg.lower()) - sum(1 for w in neg if w in msg.lower())
        lines = commit.get("stats", {}).get("total", 0)
        complexity = min(lines / 100, 1.0)
        vector = [
            sentiment * self.weights["commit_message_sentiment"],
            complexity * self.weights["code_complexity_delta"],
            0.5,
            0.3,
            0.7
        ]
        return {
            "vector": vector,
            "metadata": {
                "repo": commit.get("repo"),
                "timestamp": commit.get("timestamp", int(time.time())),
                "hash": commit.get("hash")
            }
        }

