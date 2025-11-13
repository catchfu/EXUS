import time
import requests

class CognitiveOracle:
    def __init__(self):
        self.market = {"tech_sector_sentiment": 0.72, "crypto_adoption_rate": 0.58, "ai_hiring_index": 1.34}
        self.threshold = 0.7
        self._cache = {}
        self._ttl = {"tech": 30, "crypto": 30, "fred": 60}
        self._backoff = {"tech": 0, "crypto": 0, "fred": 0}

    def get_cognitive_score(self, vector):
        sentiment = 0.65 + (time.time() % 86400) / 86400 * 0.3
        power = sum(abs(x) for x in vector) / len(vector)
        return round(power * sentiment * 10000, 2)

    def fetch_tech_sentiment(self):
        now = time.time()
        c = self._cache.get('tech')
        if c and now - c['t'] < self._ttl['tech']:
            return c['v']
        try:
            val = 0.65 + (now % 86400) / 86400 * 0.3
            self._cache['tech'] = {'v': val, 't': now}
            self._backoff['tech'] = 0
            return val
        except Exception:
            self._backoff['tech'] = min(self._backoff['tech'] + 1, 5)
            return c['v'] if c else 0.65

    def fetch_crypto_data(self):
        now = time.time()
        c = self._cache.get('crypto')
        if c and now - c['t'] < self._ttl['crypto']:
            return c['v']
        try:
            r = requests.get("https://api.coingecko.com/api/v3/global", timeout=5)
            d = r.json()["data"]
            val = {
                "market_cap": d["total_market_cap"]["usd"],
                "volume": d["total_volume"]["usd"],
                "btc_dominance": d["market_cap_percentage"]["btc"]
            }
            self._cache['crypto'] = {'v': val, 't': now}
            self._backoff['crypto'] = 0
            return val
        except Exception:
            self._backoff['crypto'] = min(self._backoff['crypto'] + 1, 5)
            return c['v'] if c else {"market_cap": 2.5e12, "volume": 1.2e11, "btc_dominance": 48.5}

    def get_market_data(self):
        return {
            "tech_sentiment": self.fetch_tech_sentiment(),
            "crypto": self.fetch_crypto_data()
        }

    def fetch_fred_data(self, series_id: str) -> float:
        now = time.time()
        key = f"fred:{series_id}"
        c = self._cache.get(key)
        if c and now - c['t'] < self._ttl['fred']:
            return c['v']
        try:
            r = requests.get("https://api.stlouisfed.org/fred/series/observations", params={"series_id": series_id, "api_key": os.getenv("FRED_API_KEY", ""), "file_type": "json", "limit": 1, "sort_order": "desc"}, timeout=5)
            v = float(r.json()["observations"][0]["value"]) if r.status_code == 200 else 0.0
            self._cache[key] = {"v": v, "t": now}
            self._backoff['fred'] = 0
            return v
        except Exception:
            self._backoff['fred'] = min(self._backoff['fred'] + 1, 5)
            return c['v'] if c else 0.0
