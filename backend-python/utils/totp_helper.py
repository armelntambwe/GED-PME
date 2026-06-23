"""TOTP (double authentification) — RFC 6238, sans dépendance externe."""
import base64
import hashlib
import hmac
import secrets
import struct
import time


def generate_secret(length=20):
    """Génère un secret Base32 pour TOTP."""
    return base64.b32encode(secrets.token_bytes(length)).decode('ascii').rstrip('=')


def _decode_base32(secret):
    s = (secret or '').upper().replace(' ', '').replace('-', '')
    pad = (8 - len(s) % 8) % 8
    s += '=' * pad
    return base64.b32decode(s)


def totp_code(secret, interval=30, digits=6, for_time=None):
    t = int(for_time if for_time is not None else time.time())
    counter = t // interval
    key = _decode_base32(secret)
    msg = struct.pack('>Q', counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack('>I', digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return str(value % (10 ** digits)).zfill(digits)


def verify_totp(secret, code, window=1):
    if not secret or not code:
        return False
    code = str(code).strip().replace(' ', '')
    if not code.isdigit() or len(code) != 6:
        return False
    now = int(time.time())
    for w in range(-window, window + 1):
        if totp_code(secret, for_time=now + w * 30) == code:
            return True
    return False


def provisioning_uri(secret, email, issuer='GED-PME'):
    label = f'{issuer}:{email}'
    from urllib.parse import quote
    return f'otpauth://totp/{quote(label)}?secret={secret}&issuer={quote(issuer)}&digits=6&period=30'
