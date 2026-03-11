"""
Symmetric encryption helpers for workspace integrations.
Uses AES-256-GCM with a master key from INTEGRATION_SECRET_KEY.
"""
import base64
import os
from typing import Optional

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


_RAW_KEY_ENV = "INTEGRATION_SECRET_KEY"
_AES_KEY_BYTES = 32
_IV_BYTES = 12


def _get_aes_key() -> bytes:
    """Derive a 32-byte AES key from INTEGRATION_SECRET_KEY."""
    secret = os.getenv(_RAW_KEY_ENV)
    if not secret:
        raise RuntimeError("INTEGRATION_SECRET_KEY is not set")

    try:
        raw = base64.b64decode(secret)
        if len(raw) == _AES_KEY_BYTES:
            return raw
    except Exception:
        pass

    digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
    digest.update(secret.encode("utf-8"))
    return digest.finalize()


def encrypt_secret(secret: Optional[str]) -> Optional[str]:
    if secret is None:
        return None

    key = _get_aes_key()
    iv = os.urandom(_IV_BYTES)

    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv),
        backend=default_backend(),
    ).encryptor()

    ciphertext = encryptor.update(secret.encode("utf-8")) + encryptor.finalize()
    payload = iv + encryptor.tag + ciphertext
    return base64.b64encode(payload).decode("utf-8")


def decrypt_secret(encrypted_secret: Optional[str]) -> Optional[str]:
    if not encrypted_secret:
        return None

    key = _get_aes_key()
    raw = base64.b64decode(encrypted_secret)
    iv = raw[:_IV_BYTES]
    tag = raw[_IV_BYTES : _IV_BYTES + 16]
    ciphertext = raw[_IV_BYTES + 16 :]

    decryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv, tag),
        backend=default_backend(),
    ).decryptor()

    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return plaintext.decode("utf-8")

