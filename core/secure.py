import os
import base64
import hashlib
from cryptography.fernet import Fernet

def _derive_key(secret: str) -> bytes:
    h = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(h)

def get_fernet() -> Fernet:
    sk = os.getenv('EXUS_SECRET') or os.getenv('SECRET_KEY') or 'exus-default-secret'
    return Fernet(_derive_key(sk))

def encrypt(s: str) -> str:
    f = get_fernet()
    return f.encrypt(s.encode()).decode()

def decrypt(s: str) -> str:
    f = get_fernet()
    return f.decrypt(s.encode()).decode()

