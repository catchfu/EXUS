import hashlib
import json
import os
import time

class ZKProver:
    def __init__(self):
        self.version = "exus_circom_v0.1"

    def create_commitment(self, vector):
        salt = os.urandom(32)
        vhash = hashlib.sha256(json.dumps(vector).encode()).digest()
        commitment = hashlib.sha256(salt + vhash).hexdigest()
        nullifier = hashlib.sha256(salt + b"exus_null").hexdigest()
        return {"commitment": commitment, "nullifier": nullifier, "salt": salt.hex(), "timestamp": int(time.time()), "version": self.version, "vector_hash": vhash.hex()}

