import json
import os
import time
from core.db import SessionLocal
from core.models import Job, CNFT, Block, OAuthToken
from miners.github_miner import GitHubMiner
from ai.extractor import CognitiveExtractor
from core.zk_prover import ZKProver
from core.blockchain import CortexChain
from core.oracle import CognitiveOracle
from core.secure import decrypt
import logging

blockchain = CortexChain()
zk = ZKProver()
oracle = CognitiveOracle()

def _get_user_token(db, username: str) -> str:
    t = db.query(OAuthToken).filter_by(username=username, provider='github').order_by(OAuthToken.created_at.desc()).first()
    if not t:
        return os.getenv('GITHUB_PAT')
    try:
        return decrypt(t.token_encrypted)
    except Exception:
        return os.getenv('GITHUB_PAT')

def process_mining_job(job_id: str, username: str, request_id: str = ""):
    db = SessionLocal()
    try:
        job = db.query(Job).get(job_id)
        job.status = 'running'
        job.updated_at = int(time.time())
        db.commit()
        logging.getLogger('job').info(json.dumps({"event":"start","job_id":job_id,"username":username,"request_id":request_id}))
        token = _get_user_token(db, username)
        miner = GitHubMiner(token=token)
        commits = miner.get_recent_commits(username)
        extractor = CognitiveExtractor()
        vectors = []
        for c in commits:
            vectors.append(extractor.analyze_commit(c)["vector"])
        avg = [sum(x)/len(x) for x in zip(*vectors)] if vectors else [0.5,0.5,0.5,0.5,0.5]
        commitment = zk.create_commitment(avg)
        token_id = blockchain.mint_cnft(username, commitment)
        score = oracle.get_cognitive_score(avg)
        blockchain.update_cnft_score(token_id, score, {"source":"job","correct":True,"reward":0})
        block = blockchain.mine("miner_"+username)
        db.merge(CNFT(token_id=token_id, owner=username, commitment=commitment["commitment"], nullifier=commitment["nullifier"], minted_at=commitment["timestamp"], cognitive_score=score, total_earnings=0.0, metadata_uri=blockchain.cNFTs[token_id]["metadata_uri"]))
        if block:
            db.add(Block(index=block["index"], timestamp=block["timestamp"], hash=block["hash"], miner=block["miner"], transactions=json.dumps(block["transactions"])) )
        job.status = 'completed'
        job.updated_at = int(time.time())
        job.result = json.dumps({"commits": commits, "commitment": commitment, "cnft": blockchain.cNFTs[token_id], "score": score, "chain": [block] if block else []})
        db.commit()
        logging.getLogger('job').info(json.dumps({"event":"complete","job_id":job_id,"username":username,"request_id":request_id}))
    except Exception as e:
        job = db.query(Job).get(job_id)
        job.status = 'failed'
        job.updated_at = int(time.time())
        job.result = json.dumps({"error": str(e)})
        db.commit()
        logging.getLogger('job').info(json.dumps({"event":"error","job_id":job_id,"username":username,"error":str(e),"request_id":request_id}))
    finally:
        db.close()
