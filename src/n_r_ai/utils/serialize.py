from __future__ import annotations
from hashlib import sha256

def state_key(obj: object) -> str:
    data = repr(obj).encode()
    return sha256(data).hexdigest()
