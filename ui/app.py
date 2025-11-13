from flask import Flask, render_template, request, jsonify, session, redirect
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from core.blockchain import CortexChain
from core.zk_prover import ZKProver
from core.oracle import CognitiveOracle
from miners.github_miner import GitHubMiner
from ai.extractor import CognitiveExtractor
from core.db import SessionLocal
from core.models import User, CNFT, Block, Job
import threading, uuid, json, time
import requests

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'exus-dev-key'
blockchain = CortexChain()
zk = ZKProver()
oracle = CognitiveOracle()
_RL = {}

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/mine', methods=['POST'])
def mine():
    data = request.json or {}
    username = data.get('username') or session.get('username') or 'demo_user'
    k = f"{request.remote_addr}:mine"
    now = time.time()
    last = _RL.get(k, 0)
    if now - last < 2:
        return jsonify({"error":"rate_limited"}), 429
    _RL[k] = now
    miner = GitHubMiner(token=session.get('github_token') or os.getenv('GITHUB_PAT'))
    commits = miner.get_recent_commits(username)
    extractor = CognitiveExtractor()
    vectors = []
    for c in commits:
        v = extractor.analyze_commit(c)["vector"]
        vectors.append(v)
    avg = [sum(x)/len(x) for x in zip(*vectors)] if vectors else [0.5,0.5,0.5,0.5,0.5]
    commitment = zk.create_commitment(avg)
    token_id = blockchain.mint_cnft(username, commitment)
    score = oracle.get_cognitive_score(avg)
    blockchain.update_cnft_score(token_id, score, {"source":"initial","correct":True,"reward":0})
    block = blockchain.mine("miner_"+username)
    db = SessionLocal()
    try:
        u = db.query(User).filter_by(username=username).first()
        if not u:
            u = User(username=username)
            db.add(u)
        db.merge(CNFT(token_id=token_id, owner=username, commitment=commitment["commitment"], nullifier=commitment["nullifier"], minted_at=commitment["timestamp"], cognitive_score=score, total_earnings=0.0, metadata_uri=blockchain.cNFTs[token_id]["metadata_uri"]))
        if block:
            db.add(Block(index=block["index"], timestamp=block["timestamp"], hash=block["hash"], miner=block["miner"], transactions=json.dumps(block["transactions"])) )
        db.commit()
    finally:
        db.close()
    return jsonify({
        "commits": commits,
        "commitment": commitment,
        "cnft": blockchain.cNFTs[token_id],
        "score": score,
        "chain": [block] if block else []
    })

@app.route('/api/login/dev', methods=['POST'])
def login_dev():
    data = request.json or {}
    username = data.get('username')
    if not username:
        return jsonify({"error":"username required"}), 400
    session['username'] = username
    db = SessionLocal()
    try:
        u = db.query(User).filter_by(username=username).first()
        if not u:
            u = User(username=username)
            db.add(u)
            db.commit()
        return jsonify({"ok":True, "username": username})
    finally:
        db.close()

def run_mining_job(job_id, username):
    db = SessionLocal()
    try:
        job = db.query(Job).get(job_id)
        job.status = 'running'
        job.updated_at = int(time.time())
        db.commit()
        miner = GitHubMiner(token=os.getenv('GITHUB_PAT'))
        commits = miner.get_recent_commits(username)
        extractor = CognitiveExtractor()
        vectors = []
        for c in commits:
            v = extractor.analyze_commit(c)["vector"]
            vectors.append(v)
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
    except Exception as e:
        job = db.query(Job).get(job_id)
        job.status = 'failed'
        job.updated_at = int(time.time())
        job.result = json.dumps({"error": str(e)})
        db.commit()
    finally:
        db.close()

@app.route('/api/mine/job', methods=['POST'])
def mine_job():
    data = request.json or {}
    username = data.get('username') or session.get('username') or 'demo_user'
    k = f"{request.remote_addr}:mine_job"
    now = time.time()
    last = _RL.get(k, 0)
    if now - last < 1:
        return jsonify({"error":"rate_limited"}), 429
    _RL[k] = now
    job_id = uuid.uuid4().hex
    db = SessionLocal()
    try:
        db.add(Job(id=job_id, type='mine', status='queued'))
        db.commit()
    finally:
        db.close()
    t = threading.Thread(target=run_mining_job, args=(job_id, username), daemon=True)
    t.start()
    return jsonify({"job_id": job_id, "status": "queued"})

@app.route('/api/job/<job_id>')
def job_status(job_id):
    db = SessionLocal()
    try:
        job = db.query(Job).get(job_id)
        if not job:
            return jsonify({"error":"not found"}), 404
        res = job.result
        return jsonify({"id": job.id, "type": job.type, "status": job.status, "result": json.loads(res) if res else None})
    finally:
        db.close()

if __name__ == '__main__':
    app.run(debug=True, threaded=True)

@app.route('/api/user/me')
def user_me():
    u = session.get('username')
    db = SessionLocal()
    try:
        count = db.query(OAuthToken).filter_by(username=u, provider='github').count()
    finally:
        db.close()
    return jsonify({"username": u, "github_connected": bool(session.get('github_token')) or count > 0})

@app.route('/api/cnft/list')
def cnft_list():
    username = session.get('username') or 'demo_user'
    db = SessionLocal()
    try:
        items = db.query(CNFT).filter_by(owner=username).all()
        return jsonify({"items": [
            {
                "token_id": i.token_id,
                "cognitive_score": i.cognitive_score,
                "minted_at": i.minted_at,
                "metadata_uri": i.metadata_uri
            } for i in items
        ]})
    finally:
        db.close()

@app.route('/api/chain/stats')
def chain_stats():
    return jsonify(blockchain.stats())

@app.route('/api/chain/blocks')
def chain_blocks():
    # Return last 10 blocks from in-memory chain for quick debug
    return jsonify({"blocks": blockchain.chain[-10:]})

@app.route('/api/market/data')
def market_data():
    return jsonify(oracle.get_market_data())

@app.route('/api/jobs')
def jobs_list():
    db = SessionLocal()
    try:
        items = db.query(Job).order_by(Job.created_at.desc()).limit(20).all()
        return jsonify({"items": [
            {"id": j.id, "type": j.type, "status": j.status, "updated_at": j.updated_at}
            for j in items
        ]})
    finally:
        db.close()

@app.route('/auth/github/start')
def auth_github_start():
    client_id = os.getenv('GITHUB_CLIENT_ID')
    redirect_uri = os.getenv('OAUTH_REDIRECT_URI', 'http://127.0.0.1:5000/auth/github/callback')
    state = uuid.uuid4().hex
    session['oauth_state'] = state
    if not client_id:
        return jsonify({"error":"GITHUB_CLIENT_ID not set"}), 400
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'repo user',
        'state': state,
        'allow_signup': 'true'
    }
    url = 'https://github.com/login/oauth/authorize'
    return redirect(url + '?' + '&'.join([f"{k}={requests.utils.quote(str(v))}" for k,v in params.items()]))

@app.route('/auth/github/callback')
def auth_github_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    if not code or state != session.get('oauth_state'):
        return jsonify({"error":"invalid_oauth_state"}), 400
    client_id = os.getenv('GITHUB_CLIENT_ID')
    client_secret = os.getenv('GITHUB_CLIENT_SECRET')
    redirect_uri = os.getenv('OAUTH_REDIRECT_URI', 'http://127.0.0.1:5000/auth/github/callback')
    headers = {'Accept':'application/json'}
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': code,
        'redirect_uri': redirect_uri,
        'state': state
    }
    try:
        r = requests.post('https://github.com/login/oauth/access_token', headers=headers, data=data, timeout=10)
        tok = r.json().get('access_token')
        if not tok:
            return jsonify({"error":"oauth_exchange_failed", "detail": r.text}), 400
        session['github_token'] = tok
        return redirect('/')
    except Exception as e:
        return jsonify({"error":"oauth_error", "detail": str(e)}), 500

@app.route('/api/user/export')
def user_export():
    username = session.get('username') or 'demo_user'
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(username=username).first()
        cnfts = db.query(CNFT).filter_by(owner=username).all()
        blocks = db.query(Block).all()
        return jsonify({
            "user": {"username": username, "exists": bool(user)},
            "cnfts": [
                {"token_id": c.token_id, "score": c.cognitive_score, "minted_at": c.minted_at,
                 "metadata_uri": c.metadata_uri}
                for c in cnfts
            ],
            "blocks": [{"index": b.index, "hash": b.hash, "timestamp": b.timestamp, "miner": b.miner} for b in blocks]
        })
    finally:
        db.close()

@app.route('/api/user/data', methods=['DELETE'])
def user_delete():
    username = session.get('username') or 'demo_user'
    db = SessionLocal()
    try:
        db.query(CNFT).filter_by(owner=username).delete()
        db.commit()
        return jsonify({"ok": True})
    finally:
        db.close()
