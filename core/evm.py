from dataclasses import dataclass

@dataclass
class EVMConfig:
    rpc_url: str = "http://127.0.0.1:8545"
    chain_id: int = 1337

class EVMClient:
    def __init__(self, cfg: EVMConfig = EVMConfig()):
        self.cfg = cfg

    def connect(self):
        return True

    def mint_cnft(self, owner_address: str, commitment: str, nullifier: str) -> str:
        return "0xDEADBEEF"

