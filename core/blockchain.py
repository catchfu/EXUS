import hashlib
import json
import time

class CortexChain:
    def __init__(self):
        self.chain = []
        self.cNFTs = {}
        self.pending = []

    def mint_cnft(self, owner, commitment):
        token_id = hashlib.sha256(f"{owner}{commitment['commitment']}{time.time()}".encode()).hexdigest()[:24]
        cnft = {
            "token_id": token_id,
            "owner": owner,
            "commitment": commitment["commitment"],
            "nullifier": commitment["nullifier"],
            "minted_at": int(time.time()),
            "cognitive_score": 0,
            "is_soulbound": True,
            "metadata_uri": f"ipfs://QmEXUS{token_id}",
            "prediction_history": [],
            "total_earnings": 0.0
        }
        self.cNFTs[token_id] = cnft
        self.pending.append({"type": "mint_cnft", "token_id": token_id, "owner": owner, "timestamp": int(time.time())})
        return token_id

    def update_cnft_score(self, token_id, new_score, result):
        if token_id in self.cNFTs:
            self.cNFTs[token_id]["cognitive_score"] = new_score
            self.cNFTs[token_id]["prediction_history"].append(result)
            if result.get("correct"):
                reward = result.get("reward", 0)
                self.cNFTs[token_id]["total_earnings"] += reward
                self.pending.append({"type": "reward", "to": self.cNFTs[token_id]["owner"], "amount": reward, "token_id": token_id})

    def mine(self, miner="miner_exus"):
        if not self.pending:
            return None
        block = {"index": len(self.chain) + 1, "timestamp": int(time.time()), "transactions": self.pending.copy(), "miner": miner}
        block_hash = hashlib.sha256(json.dumps(block).encode()).hexdigest()
        block["hash"] = block_hash
        self.chain.append(block)
        self.pending = []
        return block

    def stats(self):
        return {
            "block_height": len(self.chain),
            "total_cnft": len(self.cNFTs),
            "total_transactions": sum(len(b["transactions"]) for b in self.chain),
        }

