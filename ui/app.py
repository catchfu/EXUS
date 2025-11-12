from flask import Flask, render_template, request, jsonify
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from core.blockchain import CortexChain
from core.zk_prover import ZKProver
from core.oracle import CognitiveOracle
from miners.github_miner import GitHubMiner
from ai.extractor import CognitiveExtractor

app = Flask(__name__, template_folder='templates')
blockchain = CortexChain()
zk = ZKProver()
oracle = CognitiveOracle()

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/mine', methods=['POST'])
def mine():
    data = request.json or {}
    username = data.get('username', 'demo_user')
    miner = GitHubMiner()
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
    return jsonify({
        "commits": commits,
        "commitment": commitment,
        "cnft": blockchain.cNFTs[token_id],
        "score": score,
        "chain": [block] if block else []
    })

if __name__ == '__main__':
    app.run(debug=True, threaded=True)

