#!/usr/bin/env python3
"""
Generate local RSA keys and sample RS256 JWTs (Apigee/Ping-like) for tests.

Outputs:
- private_key.pem, public_key.pem
- token_valid.txt, token_expired.txt, token_wrong_aud.txt
"""

import base64
import json
import time
from pathlib import Path
from typing import Dict

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def write_keys(dir_path: Path) -> Dict[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    (dir_path / "private_key.pem").write_bytes(priv_pem)
    (dir_path / "public_key.pem").write_bytes(pub_pem)
    return {"private": str(dir_path / "private_key.pem"), "public": str(dir_path / "public_key.pem")}


def make_token(priv_pem: bytes, kid: str, iss: str, aud: str, scopes, ttl: int) -> str:
    now = int(time.time())
    payload = {
        "iss": iss,
        "aud": aud,
        "sub": "EBSSH",
        "jti": "uuid-here",
        "nbf": now,
        "iat": now,
        "exp": now + ttl,
        "scope": scopes,
        "client_id": "local-client",
    }
    headers = {"kid": kid, "alg": "RS256", "typ": "JWT"}
    return jwt.encode(payload, priv_pem, algorithm="RS256", headers=headers)


def main() -> None:
    out_dir = Path(__file__).parent
    keys = write_keys(out_dir)
    priv_pem = Path(keys["private"]).read_bytes()

    # Generate tokens
    valid = make_token(priv_pem, "local-key", "https://idp.example/issuer", "TSIAM", ["TSIAM-Read","TSIAM-Write"], 3600)
    expired = make_token(priv_pem, "local-key", "https://idp.example/issuer", "TSIAM", ["TSIAM-Read"], -60)
    wrong_aud = make_token(priv_pem, "local-key", "https://idp.example/issuer", "WRONG-AUD", ["TSIAM-Read"], 3600)

    (out_dir / "token_valid.txt").write_text(valid)
    (out_dir / "token_expired.txt").write_text(expired)
    (out_dir / "token_wrong_aud.txt").write_text(wrong_aud)

    print("Wrote:")
    print(" -", keys["private"])
    print(" -", keys["public"])
    print(" -", out_dir / "token_valid.txt")
    print(" -", out_dir / "token_expired.txt")
    print(" -", out_dir / "token_wrong_aud.txt")


if __name__ == "__main__":
    main()


