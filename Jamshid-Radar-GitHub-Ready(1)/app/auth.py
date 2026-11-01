"""Small self-contained credential and HMAC session implementation."""
import base64
import hashlib
import hmac
import json
import secrets
import time
from pathlib import Path


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError('Password must be at least 12 characters')
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return 'scrypt$16384$' + salt.hex() + '$' + digest.hex()


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, n, salt, expected = stored.split('$')
        if algorithm != 'scrypt' or int(n) != 16384:
            return False
        actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=int(n), r=8, p=1)
        return hmac.compare_digest(actual, bytes.fromhex(expected))
    except (ValueError, TypeError):
        return False


def load_config(config_path: Path) -> dict:
    data = json.loads(config_path.read_text(encoding='utf-8'))
    base = data.get('base_path', '')
    if not (base.startswith('/') and base.endswith('/') and base.count('/') == 2
            and all(c.isascii() and (c.isalnum() or c == '-') for c in base[1:-1])):
        raise ValueError('Invalid base_path in configuration')
    return data


def session_for(config: dict, now: int | None = None) -> str:
    now = int(time.time()) if now is None else now
    payload = json.dumps({'u': config['username'], 'exp': now + 12*3600,
                          'nonce': secrets.token_hex(8)}, separators=(',', ':')).encode()
    p64 = base64.urlsafe_b64encode(payload).rstrip(b'=').decode()
    mac = hmac.new(bytes.fromhex(config['session_secret']), p64.encode(), hashlib.sha256).hexdigest()
    return p64 + '.' + mac


def check_session(token: str | None, config: dict) -> bool:
    if not token or len(token) > 1024:
        return False
    try:
        payload, signature = token.split('.', 1)
        expected = hmac.new(bytes.fromhex(config['session_secret']), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return False
        data = json.loads(base64.urlsafe_b64decode(payload + '=' * (-len(payload) % 4)))
        return data.get('u') == config['username'] and time.time() < int(data['exp'])
    except (ValueError, TypeError, KeyError):
        return False
